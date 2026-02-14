import requests
import xml.etree.cElementTree as ET
import xmltodict


class AddressValidator:
    URL = "https://secure.shippingapis.com/ShippingAPI.dll?API=Verify&XML="

    def validate(self, addr1, addr2, city, state, zip):
        ret = {}
        keyArr = [
            "Address1",
            "Address2",
            "City",
            "CityAbbreviation",
            "State",
            "Zip5",
            "Zip4",
        ]
        try:
            xmlStr = self.constructXML(addr1, addr2, city, state, zip)
            response = requests.get(self.URL + xmlStr, timeout=10)
            response.raise_for_status()
            root = xmltodict.parse(response.content)
            if "Error" in root:
                ret["Error"] = root["Error"]["Description"]
            elif "Error" in root["AddressValidateResponse"]["Address"]:
                ret["error"] = root["AddressValidateResponse"]["Address"]["Error"][
                    "Description"
                ]
            else:
                for key in keyArr:
                    if key in root["AddressValidateResponse"]["Address"]:
                        ret[key] = root["AddressValidateResponse"]["Address"][key]
        except requests.exceptions.HTTPError as errh:
            print(errh)
            ret["error"] = errh
        except requests.exceptions.ConnectionError as errc:
            print(errc)
            ret["error"] = errc
        except requests.exceptions.Timeout as errt:
            print(errt)
            ret["error"] = errt
        except requests.exceptions.RequestException as err:
            print(err)
            ret["error"] = err
        return ret

    def constructXML(self, addr1, addr2, city, state, zip):
        root = ET.Element("AddressValidateRequest", USERID="627FUSIO4749")
        ET.SubElement(root, "Revision").text = "1"
        addr = ET.SubElement(root, "Address", ID="0")
        ET.SubElement(addr, "Address1").text = addr1
        ET.SubElement(addr, "Address2").text = addr2
        ET.SubElement(addr, "City").text = city
        ET.SubElement(addr, "State").text = state
        ET.SubElement(addr, "Zip5").text = zip
        ET.SubElement(addr, "Zip4").text = ""
        xmlstr = ET.tostring(root, encoding="unicode")
        return xmlstr
