from ..utils.apimanager import ApiManager

manager = ApiManager.getInstance()

@manager.route("/data")
async def data():
    return {"message": "Hello Data"}


 