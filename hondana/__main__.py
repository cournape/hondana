if __name__ == '__main__':
    from hondana.app import app
    # import side effect
    import hondana.views  # noqa

    app.run(debug=True)
