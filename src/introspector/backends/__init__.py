import requests
import lxml.etree as etree


def etree_to_dict(t):
    d = {t.tag: list(map(etree_to_dict, t.iterchildren()))}
    d.update(("@" + k, v) for k, v in t.attrib.iteritems())
    if len(d[t.tag]) == 0:
        d[t.tag] = t.text
        return d
    d[t.tag].sort(key=lambda x: list(x.keys())[0])
    if len(d[t.tag]) == 1:
        d[t.tag] = d[t.tag][0]
    if t.text:
        d["text"] = t.text
    if len(d[t.tag]) > 1 and {type(e) for e in d[t.tag]} == {dict}:
        flat_dict = dict(list(i.items())[0] for i in d[t.tag])
        if len(flat_dict) == len(d[t.tag]):
            d[t.tag] = flat_dict
    return d


def soap_response_to_dict(response: requests.Response) -> dict:
    doc = etree.parse(response.raw)
    return etree_to_dict(doc.getroot())
