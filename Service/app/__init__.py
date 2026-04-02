from .utils.apimanager import ApiManager
from .routes import *

manager = ApiManager.getInstance()

app = manager.setup('flask').app
   
@manager.route("/")
async def index():
    return {"message": "Hello World"}

