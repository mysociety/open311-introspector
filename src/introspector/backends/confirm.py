from typing import Iterable, Tuple
from html import escape
from functools import cache

import requests

from ..backends import soap_response_to_dict


class ConfirmBackend:
    config: dict

    def __init__(self, config: dict):
        self.config = config

    def operation_request_as_dict(self, operation):
        response = self.make_operation_request(operation)
        parsed = soap_response_to_dict(response)
        return parsed["{http://schemas.xmlsoap.org/soap/envelope/}Envelope"][
            "{http://schemas.xmlsoap.org/soap/envelope/}Body"
        ][
            "{http://www.confirm.co.uk/schema/am/connector/webservice}ProcessOperationsResult"
        ][
            "Response"
        ][
            "OperationResponse"
        ]

    def make_operation_request(self, *operations: Iterable[str]) -> requests.Response:
        url = self.config["endpoint_url"]
        tenant = self.config["tenant_id"]
        username = self.config["username"]
        password = self.config["password"]
        if not all((url, tenant, username, password)):
            raise ValueError(
                "Config not complete; please ensure the following are all specified: endpoint_url, username, password, tenant_id"
            )
        operations_xml = "\n".join(
            f"<Operation>{operation}</Operation>" for operation in operations
        )
        request_body = f"""<?xml version='1.0' encoding='utf-8'?>
    <soap-env:Envelope
        xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:web="http://www.confirm.co.uk/schema/am/connector/webservice">
        <soap-env:Body>
            <web:ProcessOperationsRequest>
                <Request>
                    <Authentication>
                        <Username>{username}</Username>
                        <Password>{escape(password)}</Password>
                        <DatabaseId>{tenant}</DatabaseId>
                    </Authentication>
                    {operations_xml}
                </Request>
            </web:ProcessOperationsRequest>
        </soap-env:Body>
    </soap-env:Envelope>
    """.encode(
            "utf-8"
        )
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Soapaction": "http://www.confirm.co.uk/schema/am/connector/webservice/ProcessOperations",
        }
        return requests.post(url, request_body, headers=headers, stream=True)

    @cache
    def GetEnquiryLookups(self):
        return self.operation_request_as_dict(
            """<GetEnquiryLookups></GetEnquiryLookups>"""
        )["GetEnquiryLookupsResponse"]

    @cache
    def GetCustomerLookups(self):
        return self.operation_request_as_dict(
            """<GetCustomerLookups></GetCustomerLookups>"""
        )["GetCustomerLookupsResponse"]

    def get_status_codes(self) -> Iterable[Tuple[str, str, bool, bool]]:
        statuses = []
        for item in self.GetEnquiryLookups():
            if not "EnquiryStatus" in item:
                continue
            code = name = outstanding = inactive = None
            if isinstance(item["EnquiryStatus"], dict):
                item["EnquiryStatus"] = [item["EnquiryStatus"]]
            for part in item["EnquiryStatus"]:
                statuses.append(
                    (
                        part.get("EnqStatusCode"),
                        part.get("EnqStatusName"),
                        part.get("OutstandingFlag", "") == "true",
                        bool(part.get("Inactive", False)),
                    )
                )
        return statuses

    def get_enquiry_methods(self) -> Iterable[Tuple[str, str]]:
        methods = []
        for item in self.GetCustomerLookups():
            if not "EnquiryMethod" in item:
                continue
            item = item["EnquiryMethod"]
            methods.append(
                (item.get("EnquiryMethodCode"), item.get("EnquiryMethodName"))
            )
        return methods

    def get_customer_types(self) -> Iterable[Tuple[str, str]]:
        types = []
        for item in self.GetCustomerLookups():
            if not "CustomerType" in item:
                continue
            item = item["CustomerType"]
            types.append((item.get("CustomerTypeCode"), item.get("CustomerTypeName")))
        return types

    def get_point_of_contact_codes(self) -> Iterable[Tuple[str, str]]:
        types = []
        for item in self.GetCustomerLookups():
            if not "PointOfContact" in item:
                continue
            item = item["PointOfContact"]
            types.append(
                (item.get("PointOfContactCode"), item.get("PointOfContactName"))
            )
        return types

    def get_service_subject_codes(self) -> Iterable[Tuple[str, str, str, str]]:
        codes = []
        for item in self.GetEnquiryLookups():
            if not "TypeOfService" in item:
                continue
            if isinstance(item["TypeOfService"], dict):
                item["TypeOfService"] = [item["TypeOfService"]]
            code = name = None
            subjects = []
            for part in item["TypeOfService"]:
                if "ServiceCode" in part:
                    code = part["ServiceCode"]
                if "ServiceName" in part:
                    name = part["ServiceName"]
                if "EnquirySubject" in part:
                    subject = part["EnquirySubject"]
                    sname = scode = None
                    for entry in subject:
                        if entry == "SubjectCode":
                            scode = subject["SubjectCode"]
                        elif "SubjectCode" in entry:
                            scode = entry["SubjectCode"]
                        if entry == "SubjectName":
                            sname = subject["SubjectName"]
                        elif "SubjectName" in entry:
                            sname = entry["SubjectName"]
                    if sname and scode:
                        subjects.append((scode, sname))
            codes.extend([(code, name, scode, sname) for scode, sname in subjects])
        return codes
