import json

from rest_framework.renderers import JSONRenderer


class BonusResponseRenderer(JSONRenderer):
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        message = 'successfully done.'
        if not isinstance(data, list):
            errors = data.get('errors', None)
            detail = data.get('detail', None)
            if errors is not None:
                message = json.dumps(errors)
                if isinstance(message, dict):
                    if len(message) == 1 and message.get("error") is not None:
                        message = str(message["error"]).replace('[', '').replace(']', '').replace('\'', '')
                    else:
                        for x in message:
                            message[x] = str(message[x]).replace('[', '').replace(']', '').replace('\'', '')
                elif isinstance(message, list):
                    message = str(message).replace('[', '').replace(']', '').replace('\'', '')
                data = None
            elif detail is not None:
                data = None
                message = ""
                message = get_the_string(errors, message)
                message += get_the_string(detail, message)
        return json.dumps({
            'data': data,
            'message': message
        })


def get_the_string(data, message):
    if data is None:
        return ''
    if isinstance(data, dict):
        for x in data:
            message = get_the_string(data[x], message)
    elif isinstance(data, list):
        for x in data:
            message = get_the_string(x, message)
    else:
        return str(data) + ' ' + message
    return message
