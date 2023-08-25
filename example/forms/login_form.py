from weba import app, ui


class BaseForm:
    pass


class LoginForm(BaseForm):
    @classmethod
    def ui(cls):
        return ui.div("Login Form")


@app.form()
def login_form():
    return ui.div("Login Form")
