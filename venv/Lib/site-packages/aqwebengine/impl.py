
'''
Qt provides a qt.webChannelTransport, that has send() method and allows assigning to onmessage property.

send(String) - sends JSON.stringify'd object to the python side. Object must have the following properties:
    * id: - unique id to correlate response
    * type: 6 (method call)
    * object - the name of object registered with QWebChannel (we use "bridge" here)
    * method - the name of the method to call
    * args - an array of arguments (we use a single argument - a stringify'd JSON)
'''
_AQWEBENGINE_JS = '''(() => {
    if (window.qt === undefined || window.qt.webChannelTransport === undefined) {
        console.error('No qt.webChannelTransport found')
        return;
    }

    const transport = window.qt.webChannelTransport;
    const locals = { callId: 0 };
    const reply = { };

    transport.onmessage = () => {};

    // JS call Python
    function callPython(name, params) {
        if (params === undefined) params = null;
        const callId = locals.callId++;
        return new Promise( (resolve, reject) => {
            reply[callId] = { resolve, reject };
            const message = {
                id: 777,
                type: 6,
                object: 'bridge',
                method: 'call_python',
                args: [callId, JSON.stringify({
                    name: name,
                    params: params,
                })]
            };
            // console.log("sending (callPython)", message);
            transport.send(JSON.stringify(message));
        });
    }

    // Python calls JS, and JS asynchronously calls this to complete asynchronous Python call
    function jsReply(callId, value) {
        if (value === undefined) value = null;
        const message = {
            id: callId,
            type: 6,
            object: 'bridge',
            method: 'js_reply',
            args: ['' + callId, JSON.stringify(value || null)],
        };
        // console.log("sending (jsReply)", message);
        transport.send(JSON.stringify(message));
    }

    // JS calls Python as Python calls this to complete asynchronous JS call.
    function pythonReply(callId, valueString) {
        // console.log('PYTHON replied:', callId, valueString);

        if (reply[+callId]) {
            const data = JSON.parse(valueString);
            const promise = reply[+callId];
            delete reply[+callId];

            if (data.error) {
                return promise.reject(data.error);
            } else {
                return promise.resolve(data.result);
            }
        }
    }

    window.qt.callPython = callPython;
    window.qt._jsReply = jsReply;
    window.qt._pythonReply = pythonReply;

    return callPython('bridge-is-ready');
})();
'''
import json
import uuid
import functools
import asyncio
import inspect
import sys
from .qtx import QIODevice, QFile, QWebEngineView, QWebEngineScript, QWebChannel, Slot, QObject, QUrl, QWebEngineSettings


def _script(name, js, injectionPoint=QWebEngineScript.DocumentReady):
    s = QWebEngineScript()
    s.setSourceCode(js)
    s.setName(name)
    s.setWorldId(QWebEngineScript.MainWorld)
    s.setInjectionPoint(injectionPoint)
    s.setRunsOnSubFrames(True)
    return s


class _Bridge(QObject):
    def __init__(self, call_python, js_eval, on_js_eval_reply):
        super().__init__()
        self._call_python = call_python
        self._js_eval = js_eval
        self._on_js_eval_reply = on_js_eval_reply

    @Slot(str, str)
    def call_python(self, caller_id, json_string):
        '''This method facilitates async communication from JS to Python'''

        async def handle(json_string):
            return await self._call_python(json.loads(json_string))

        def done_callback(caller_id, task):
            try:
                result = {
                    'result': task.result(),
                }
            except BaseException as err:
                result = {
                    'error': str(err),
                }
            result = json.dumps(result)
            self._js_eval(f'window.qt._pythonReply({repr(caller_id)}, {repr(result)});')

        task = asyncio.get_running_loop().create_task(handle(json_string))
        task.add_done_callback(functools.partial(done_callback, caller_id))

    @Slot(str, str)
    def js_reply(self, caller_id, json_string):
        '''This method facilitates async communication from Python to JS'''
        asyncio.create_task(self._on_js_eval_reply(caller_id, json_string))


class JSError(RuntimeError): pass



class AQWebEngineView(QWebEngineView):

    def set_font_family(self, family):
        '''Convenience shortcut to set default font name'''
        self.page().settings().setFontFamily(QWebEngineSettings.StandardFont, family)

    def set_font_size(self, size):
        '''Convenience shortcut to set default font size'''
        self.page().settings().setFontSize(QWebEngineSettings.DefaultFontSize, size)

    def __init__(self, *av, **kav):
        super().__init__(*av, **kav)

        self._channel = QWebChannel()
        self.page().setWebChannel(self._channel)

        self._bridge = _Bridge(self._call_python, self.page().runJavaScript, self._on_eval_js_reply)
        self._channel.registerObject('bridge', self._bridge)

        self._reply = {}
        self._reply_ready = asyncio.Condition()

        self._set_content_lock = asyncio.Lock()

        self._registered_python_functions = {}

        self._inited = asyncio.Event()

    async def init(self):
        '''Initialize 2-way communication machinery between Python host and JS guest'''

        if self._inited.is_set():
            raise RuntimeError('alreadey inited')


        self.page().profile().scripts().insert(
            _script(
                'AQWebengine.js',
                _AQWEBENGINE_JS,
                injectionPoint=QWebEngineScript.DocumentCreation
            )
        )

        self.setHtml('')

        while not self._inited.is_set():
            await self._inited.wait()
        await asyncio.sleep(0.1)

    async def eval_js(self, js_script):
        '''Calls JS guest, evaluating the string.

        String can be any valid JS expression, evaluating to a value or promise. One particularly
        convenient idiom is to use self-evaluating function block, example:

            js_script = """(async ()=>{
                const response = await fetch("https://www.google.com");
                return await response.text();
            })()"""
        '''
        if not self._inited.is_set():
            raise RuntimeError('Not inited. Did you forget to call "await init()" on me?')

        id_ = str(uuid.uuid4())
        async with self._reply_ready:
            self.page().runJavaScript(f'''(async () => {{
                try {{
                    const value = await Promise.resolve(eval({repr(js_script)}));
                    return {{
                        id: "{id_}",
                        value: value,
                    }};
                }} catch(err) {{
                    console.error('ERR: ' + err);
                    console.error(err.stack);
                    return {{
                        id: "{id_}",
                        error: 'JS: ' + err,
                    }};
                }}
            }})().then(value => qt._jsReply("{id_}", value));''')
            while True:
                if id_ in self._reply:
                    value = self._reply.pop(id_)
                    if value.get('error') is not None:
                        raise JSError(value['error'])
                    return value.get('value')
                try:
                    await self._reply_ready.wait()
                except asyncio.exceptions.CancelledError:
                    return None

    async def _on_eval_js_reply(self, caller_id, json_string):
        params = json.loads(json_string)
        async with self._reply_ready:
            self._reply[caller_id] = params
            self._reply_ready.notify_all()

    def register_python_function(self, name, async_callable):
        '''Register python function to expose it to the JS callers.

        Function should take a single argument of any JSON-serializable type. It can be sync or async.

        Example:

            w = QWebEngineView()
            await w.init()

            def f(message):
                print(message)
                return 42

            w.register_python_function('my_function_name', f)
            w.page().runJavaScript("""( async () => {
                const response = await window.qt.callPython("my_function_name", "Hello, world");
                console.error("Python function my_function_name returned", response);
            })()""")

        '''
        self._registered_python_functions[name] = async_callable

    async def _call_python(self, event):
        if event['name'] == 'bridge-is-ready':
            self._inited.set()
        elif event['name'] in self._registered_python_functions:
            afn = self._registered_python_functions[event['name']]
            result = afn(event['params'])
            if inspect.iscoroutine(result):
                result = await result
            return result
        else:
            raise RuntimeError(f'Python function {event["name"]} is not registered')

    async def set_html_async(self, html, base_url=None):
        '''Loads HTML text, asynchronously'''
        async with self._set_content_lock:
            f = asyncio.Future()
            def handler(percent):
                if percent == 100:
                    f.set_result(None)
            self.loadProgress.connect(handler)
            try:
                if base_url is not None:
                    self.setHtml(html, QUrl(base_url))
                else:
                    self.setHtml(html)
                await f
            finally:
                self.loadProgress.disconnect(handler)

    async def load_async(self, url):
        '''Loads URL, asynchronously'''
        async with self._set_content_lock:
            f = asyncio.Future()
            def handler(percent):
                if percent == 100:
                    f.set_result(None)
            self.loadProgress.connect(handler)
            try:
                import os
                self.load(QUrl(url))
                await f
            finally:
                self.loadProgress.disconnect(handler)

    async def to_html_async(self):
        '''Retrieve current page source, as HTML'''
        f = asyncio.Future()
        self.page().toHtml(f.set_result)
        await f
        return f.result()

    async def to_plain_text_async(self):
        '''Retrieve current page source, as plain text'''
        f = asyncio.Future()
        self.page().toPlainText(f.set_result)
        await f
        return f.result()


def async_slot(fn):
    '''Wrapper for async functions to make them synchronous. Qt signals can only connect to synchronous functions.

    Example:

        @async_slot
        async def do_something():
            await asyncio.sleep(10)

        ...
        push_button.clicked.connect(do_something)
    '''

    @functools.wraps(fn)
    def wrapper(*av, **kav):
        def handle_done(task):
            try:
                task.result()
            except asyncio.exceptions.CancelledError:
                pass
            except Exception:
                sys.excepthook(*sys.exc_info())

        task = asyncio.create_task(fn(*av, **kav))
        task.add_done_callback(handle_done)

    return wrapper
