from clarifai.rest import ClarifaiApp


class Predict:
    app = None
    model = None

    def __init__(self, api_key: str = None):
        self.app = ClarifaiApp(api_key=api_key)
        self.model = self.app.public_models.general_model

    def check(self, logger, url: str = None, tags: list = [], tags_skip: list = [], is_video: bool = False):
        try:
            concepts = self.get(url=url, is_video=is_video)
            if len(tags_skip) > 0:
                if any((tag in concepts for tag in tags_skip)):
                    logger.info(
                        'Not interacting, image contains concept(s): "{}".'.format(
                            ", ".join(list(set(concepts) & set(tags_skip)))
                        )
                    )
                    return False
                else:
                    return any((tag in concepts for tag in tags))
        except Exception as err:
            self.logging.info("Ops, something wrong on clarifai predict, sorry.")
            self.logging.error(err)
            pass

    def get(self, url, is_video=False):
        try:
            response = self.model.predict_by_url(url=url, is_video=is_video)
            if response['status']['code'] == 10000:
                r = []
                if is_video:
                    for frame in response['outputs'][0]['data']['frames']:
                        for concept in frame['data']['concepts']:
                            r.append(concept['name'])
                else:
                    for concept in response['outputs'][0]['data']['concepts']:
                        r.append(concept['name'])
            r = list(dict.fromkeys(r))

        except Exception as e:
            return False
            pass
        return r
