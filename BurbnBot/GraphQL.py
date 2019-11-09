import json
from urllib.request import urlopen


class GraphQl:

    def get_data(self, type, p):
        if type == "tags":
            url = "https://www.instagram.com/explore/tags/{}/?__a=1".format(p)
        elif type == "post":
            url = "{}?__a=1".format(p)

        json_url = urlopen(url=url)
        if json_url.status == 200:
            return json.loads(json_url.read())
        else:
            return False

    def tags(self, tag: str = "", aba: str = ""):
        data = self.get_data(type="tags", p=tag)
        if aba.lower() == "top":
            edge_hashtag = "edge_hashtag_to_top_posts"
        else:
            edge_hashtag = "edge_hashtag_to_media"

        return data['graphql']['hashtag'][edge_hashtag]['edges']

    def post_info(self, url: str = None):
        data = self.get_data(type="post", p=url)
        if data['graphql']['shortcode_media']['is_video']:
            media_url = data['graphql']['shortcode_media']['video_url']
        else:
            media_url = data['graphql']['shortcode_media']['display_url']
        r = {
            "is_video": data['graphql']['shortcode_media']['is_video'],
            "is_video": data['graphql']['shortcode_media']['is_video'],
            "is_ad": data['graphql']['shortcode_media']['is_ad'],
            "media_url": media_url
        }
        return r
