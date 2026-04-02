from ultralytics import YOLO
import pathlib

MODULE_PATH = pathlib.Path(__file__).parent

MODEL_PATH = MODULE_PATH / 'model/yolo_best.pt'
TEMP_DIR = MODULE_PATH / 'temp'
RESULTS_DIR = MODULE_PATH / 'results'
TEST_IMG_DIR = MODULE_PATH / 'test_img'


def predict(img_path):
    print('加载YOLO模型...')
    model = YOLO(MODEL_PATH)
    print('模型加载完成')
    model.predict(
        source=img_path,
        project=RESULTS_DIR,
        save=True,
        show=True,
        conf=0.5,
    )
    
if __name__ == '__main__':
    predict(TEST_IMG_DIR / 'Xinxiang_Wheat_S2_Fused_202304-0000000000-0000000000_1920_3456.png')
