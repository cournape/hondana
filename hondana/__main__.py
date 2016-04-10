import os.path


if __name__ == '__main__':
    from hondana.app import app
    import hondana.views

    app.run(debug=True)
