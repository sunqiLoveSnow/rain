from rain.client import remote, RainException, Program, Input, blob
import pytest
import pickle

def test_remote_bytes_inout(test_env):
    """Pytask taking and returning bytes"""

    @remote()
    def hello(ctx, data):
        return data.to_bytes() + b" rocks!"

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = hello(blob("Rain"))
        t1.output.keep()
        s.submit()
        assert b"Rain rocks!" == t1.output.fetch()


def test_remote_more_bytes_outputs(test_env):
    """Pytask returning more tasks"""

    @remote(outputs=("x1", "x2"))
    def test(ctx):
        return {"x1": b"One", "x2": b"Two"}

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        t1.outputs["x1"].keep()
        t1.outputs["x2"].keep()
        s.submit()
        assert b"One" == t1.outputs["x1"].fetch()
        assert b"Two" == t1.outputs["x2"].fetch()


def test_remote_exception(test_env):

    # TODO: Check error message
    # but "match" in pytest.raises somehow do not work??

    @remote()
    def test(ctx):
        raise Exception("Hello world!")

    test_env.start(1)

    for i in range(10):
        with test_env.client.new_session() as s:
            t1 = test()
            t1.output.keep()
            s.submit()

            with pytest.raises(RainException):
                t1.wait()
            with pytest.raises(RainException):
                t1.wait()
            with pytest.raises(RainException):
                t1.output.fetch()


def test_remote_exception_sleep(test_env):

    @remote()
    def test(ctx):
        import time
        time.sleep(0.2)
        raise Exception("Hello world!")

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        t1.output.keep()
        s.submit()
        with pytest.raises(RainException):
            t1.wait()
        with pytest.raises(RainException):
            t1.wait()
        with pytest.raises(RainException):
                t1.output.fetch()


def test_remote_exception_fetch_after_delay(test_env):
    import time

    @remote()
    def test(ctx):
        raise Exception("Hello world!")

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        t1.output.keep()
        s.submit()
        time.sleep(0.6)
        with pytest.raises(RainException):
            t1.output.fetch()
        with pytest.raises(RainException):
            t1.output.fetch()
        with pytest.raises(RainException):
            t1.wait()


def test_remote_exception_fetch_immediate(test_env):

    @remote()
    def test(ctx):
        import time
        time.sleep(0.3)
        raise Exception("Hello world!")

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        t1.output.keep()
        s.submit()
        with pytest.raises(RainException):
            t1.output.fetch()
        with pytest.raises(RainException):
            t1.output.fetch()
        with pytest.raises(RainException):
            t1.wait()


def test_python_invalid_output(test_env):

    @remote()
    def test(ctx):
        class X():
            pass
        return X()

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        s.submit()
        with pytest.raises(RainException):
            t1.wait()


def test_string_output(test_env):

    @remote()
    def test(ctx):
        return "Hello world!"

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        t1.output.keep()
        s.submit()
        assert b"Hello world!" == t1.output.fetch()


def test_py_file_output(test_env):
    @remote()
    def test(ctx):
        import os
        assert not os.listdir(".")
        with open("test_file", "w") as f:
            f.write("Hello world!")
        f = ctx.stage_file("test_file")
        assert not os.listdir(".")
        return f

    test_env.start(1)
    with test_env.client.new_session() as s:
        t1 = test()
        t1.output.keep()
        s.submit()
        assert b"Hello world!" == t1.output.fetch()


def test_py_pass_through(test_env):
    @remote(outputs=("out1", "out2"))
    def test(ctx, data1, data2):
        return {"out1": data1, "out2": data2}

    test_env.start(1)

    cat = Program("/bin/cat input1", stdout="output", inputs=[Input("input1")])

    with test_env.client.new_session() as s:
        data = b"ABC" * 10000
        t0 = cat(input1=data)
        t1 = test(t0, "Hello!")
        t1.outputs["out1"].keep()
        t1.outputs["out2"].keep()
        s.submit()
        assert data == t1.outputs["out1"].fetch()
        assert b"Hello!" == t1.outputs["out2"].fetch()


def test_py_ctx_debug(test_env):
    @remote()
    def test(ctx):
        ctx.debug("First message")
        ctx.debug("Second message")
        ctx.debug("Last message")
        return b"Result"

    test_env.start(1)
    with test_env.client.new_session() as s:
        t0 = test()
        s.submit()
        t0.wait()
        t0.update()
        assert t0.get("debug") == "First message\nSecond message\nLast message"


def test_py_ctx_set(test_env):
    @remote()
    def test(ctx):
        ctx.set("string", "value")
        ctx.set("int", 103)
        ctx.set("float", 77.12)
        ctx.set("boolTrue", True)
        ctx.set("boolFalse", False)
        ctx.set("data", b"ABC")
        return b"Test"

    test_env.start(1)
    with test_env.client.new_session() as s:
        t0 = test()
        s.submit()
        t0.wait()
        t0.update()
        assert t0.get("string") == "value"
        assert t0.get("int") == 103
        assert t0.get("float") == 77.12
        assert t0.get("boolTrue") is True
        assert t0.get("boolFalse") is False
        assert t0.get("data") == b"ABC"

def test_remote_complex_args(test_env):

    @remote()
    def test(ctx, a, b, c={}, d=0, **kwargs):
        ret = (a, b.to_bytes(), c['a'].to_bytes(), c['b'][3].to_bytes(), d, kwargs['e'](4).to_bytes())
        return pickle.dumps(ret)

    test_env.start(1)
    with test_env.client.new_session() as s:

        bs = [blob(str(i)) for i in range(5)]
        t0 = test([True], bs[0], {"a": bs[1], "b": bs}, d=42, e=lambda x: bs[x])
        t0.output.keep()
        s.submit()
        d = t0.output.fetch()
        assert pickle.loads(d) == ([True], b'0', b'1', b'3', 42, b'4')



