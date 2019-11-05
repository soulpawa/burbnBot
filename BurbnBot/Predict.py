from clarifai.rest import ClarifaiApp


class Predict:
    def __init__(self, api_key: str = None):
        self.app = ClarifaiApp(api_key=api_key)

        self.model = self.app.public_models.general_model

    def get(self, base64_bytes: str = None):
        response = self.model.predict_by_base64(base64_bytes=base64_bytes)
        breakpoint()
