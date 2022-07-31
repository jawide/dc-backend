def check(text) -> bool:
    '''
    检查文本内容是否符合docker-compose标准
    '''
    return True

class LackJSONParameter(Exception):
    def __init__(self, names, index) -> None:
        super().__init__('Lack json parameter "{}"'.format('.'.join(names[:index+1])))

def get_from_json(json, *names):
    if json is None:
        raise LackJSONParameter(['...'], 0)
    c = json
    for i, name in enumerate(names):
        try:
            c = json[name]
        except KeyError:
            raise LackJSONParameter(names, i)
    return c