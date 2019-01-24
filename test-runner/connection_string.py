#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import urllib
import hmac
import hashlib
import time
import base64


def get_auth_token(uri, sas_name, sas_value):
    """
  Given a URI, a sas_name, and a sas_value, return a shared access signature.
  """
    sas = base64.b64decode(sas_value)
    expiry = str(int(time.time() + 10000))
    string_to_sign = (uri + "\n" + expiry).encode("utf-8")
    signed_hmac_sha256 = hmac.HMAC(sas, string_to_sign, hashlib.sha256)
    signature = urllib.parse.quote(base64.b64encode(signed_hmac_sha256.digest()))
    return "SharedAccessSignature sr={}&sig={}&se={}&skn={}".format(
        uri, signature, expiry, sas_name
    )


def connectionStringToDictionary(str):
    """
  parse a connection string and return a dictionary of values
  """
    cn = {}
    for pair in str.rstrip("=").split(";"):
        (key, value) = pair.split("=")
        cn[key] = value
    return cn


def parseConnectionString(str):
    """
  parse an IoTHub service connection string and return the host and a shared access
  signature that can be used to connect to the given hub
  """
    cn = connectionStringToDictionary(str)
    sas = get_auth_token(
        cn["HostName"], cn["SharedAccessKeyName"], cn["SharedAccessKey"] + "="
    )
    return {"host": cn["HostName"], "sas": sas}
