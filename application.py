import flaskr

application = flaskr.create_app()

if '__main__' == __name__:
    application.debug = False
    application.run()
