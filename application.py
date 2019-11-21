import flaskr

application = flaskr.create_app()

if '__main__' == __name__:
    application.debug = True #TODO: turn this off in production
    application.run()

