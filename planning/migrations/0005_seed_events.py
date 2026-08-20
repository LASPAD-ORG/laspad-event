from django.db import migrations

# Import unique de l'historique des événements du labo, depuis l'export du
# Google Sheet interne (snapshot d'août 2026, 33 événements d'avril 2026).
# Le CSV est encodé en base64 pour ne dépendre d'aucun réseau au déploiement.
# Idempotent : ne fait rien si un import a déjà eu lieu (created_by=import@laspad.org).

import base64
import csv
import datetime
import io

CSV_B64 = (
        "UHJvamV0LFR5cGUsVGl0cmUgZGUgbCfDqXbDqG5lbWVudCxEZXNjcmlwdGlvbiAsRGF0ZSBkZSBkw6lidXQsSGV1cmUsRGF0ZSBk"
        "ZSBmaW4sUmVzcG9uc2FibGUgLEludml0w6lzLEJlc29pbnMgZGUgY29tbXVuaWNhdGlvbiAsQmVzb2luIGRlIHByb2R1dGlvbiAs"
        "TGlldSxTdGF0dXMgY29sdW1uLCxCdWRnZXQgVmFsaWTDqQ0KQ291cnMgTWVkaXRzLEZvcm1hdGlvbizDiXZhbHVhdGlvbiBldCBp"
        "bnTDqWdyaXTDqSBzY2llbnRpZmlxdWUgKFByIFNhcmEgTWVqZG91YmkpLENvdXJzLDA2LzA0LzIwMjYsMTc6MDA6MDAsLE1hbWFk"
        "b3UgTGFtaW5lIERpYW5keSwsLCxFbiBsaWduZSxSZXBvcnTDqSBhdSBtZXJjcmVkaSA4IGF2cmlsIDIwMjYsLA0KQ291cnMgTWVk"
        "aXRzLEZvcm1hdGlvbixMJ8OpcXVpcGUgw6lkaXRvcmlhbGUgKENlbGluZSBCYXJ0aG9ubmF0KSxDb3VycywwNy8wNC8yMDI2LDE3"
        "OjAwOjAwLDE4OjMwOjAwLE1hbWFkb3UgTGFtaW5lIERpYW5keSwsLCxFbiBsaWduZSxGYWl0LCwNCixSZWNydXRlbWVudCxFbnRy"
        "ZXRpZW4gYXZlYyBkZXMgc3RhZ2lhaXJlcyBwb3RlbnRpZWxzLEVudHJldGllbnMgZGUgcmVjcnV0ZW1lbnQsMDcvMDQvMjAyNiww"
        "OTowMDowMCwxMjozMDowMCxBeXJ0b24gQXVicnksLCwsRW4gbGlnbmUsLCwNClPDqW1pbmFpcmUsU8OpbWluYWlyZSAsRMOpcGVu"
        "ZGFuY2UgdGVjaG5vbG9naXF1ZSBldCBmYWlibGVzc2UgZGUgbOKAmWlubm92YXRpb24gaW5kdXN0cmllbGxlIGVuIGFmcmlxdWUs"
        "U2VtaW5haXJlIGRvY3RvcmFsZSBkZSBsJ2F4ZSBwb2xpdGlxdWVzIHRlY2hub2xvZ2lxdWVzIGV0IHNvdXZlcmFpbmV0w6ksMDcv"
        "MDQvMjAyNiwxMDozMDowMCwxMjozMDowMCxTdGFuaXNsYXMgR29tZXMsLCxwb3N0LXByb2R1Y3Rpb24sRW4gbGlnbmUsLCwNClVQ"
        "QU5aSSxSZXVuaW9uLFVQQU5aSSxSZXVuaW9uICwwNy8wNC8yMDI2LDEzOjAwOjAwLDE1OjAwOjAwLFN0YW5pc2xhcyBHb21lcyws"
        "LCxFbiBsaWduZSwsLA0KTXVsdGlsYXTDqXJhbGlzbWUsUsOpdW5pb24sUsOpdW5pb24gSGViZG9tYWRhaXJlLFLDqXVuaW9uIGRl"
        "IHRyYXZhaWwsMDgvMDQvMjAyNiwxMDowMDowMCwxMTowMDowMCxBeXJ0b24gQXVicnksRXF1aXBlIGR1IE5BQU0sLCxTdXIgcGxh"
        "Y2UgKGJ1cmVhdSBkZSBsYSBkaXJlY3Rpb24pLCwsDQpNdWx0aWxhdMOpcmFsaXNtZSxUYWJsZSByb25kZSxUYWJsZSByb25kZSxU"
        "YWJsZSByb25kZSBhdmVjIGxlIG1pbmlzdMOocmUgZGVzIGFmZmFpcmVzIMOpdHJhbmfDqHJlcyBzdXIgbGEgdGjDqW1hdGlxdWUg"
        "ZHUgcGFuYWZyaWNhbmlzbWUsMDgvMDQvMjAyNiwxNTowMDowMCwxODowMDowMCxBeXJ0b24gQXVicnksLEFmZmljaGUgKyBkaWZm"
        "dXNpb24gZGUgbCdpbmZvcm1hdGlvbiBzdXIgbGVzIHLDqXNlYXV4IGR1IExBU1BBRCArIE1haWxjaGltcCwsIlNpw6hnZSBkdSBN"
        "SUFFU0UsIHBsYWNlIGRlIGwnaW5kw6lwZW5kZW5jZSIsLCwNCkNvdXJzIE1lZGl0cyxGb3JtYXRpb24sw4l2YWx1YXRpb24gZXQg"
        "aW50w6lncml0w6kgc2NpZW50aWZpcXVlIChQciBTYXJhIE1lamRvdWJpKSxDb3VycywwOC8wNC8yMDI2LDE3OjAwOjAwLCxNYW1h"
        "ZG91IExhbWluZSBEaWFuZHksLCwsRW4gbGlnbmUsRmFpdCwsDQpDb3VycyBNZWRpdHMsRm9ybWF0aW9uLEwnw6lxdWlwZSDDqWRp"
        "dG9yaWFsZSAoQ2VsaW5lIEJhcnRob25uYXQpLENvdXJzLDA5LzA0LzIwMjYsMTc6MDA6MDAsMTg6MzA6MDAsTWFtYWRvdSBMYW1p"
        "bmUgRGlhbmR5LCwsLEVuIGxpZ25lLCwsDQpDb3VycyBNZWRpdHMsRm9ybWF0aW9uLMOJdmFsdWF0aW9uIGV0IGludMOpZ3JpdMOp"
        "IHNjaWVudGlmaXF1ZSAoUHIgU2FyYSBNZWpkb3ViaSksQ291cnMsMTAvMDQvMjAyNiwxNzowMDowMCwsTWFtYWRvdSBMYW1pbmUg"
        "RGlhbmR5LCwsLEVuIGxpZ25lLCwsDQpTw6ltaW5haXJlLFPDqW1pbmFpcmUgLCxTZW1pbmFpcmUgYXZlYyBsZSBkaXJlY3RldXIg"
        "ZGVzIHRyYXZhdXggZGUgQVBJWCwxMS8wNC8yMDI2LDEyOjAwOjAwLDE0OjAwOjAwLFN0YW5pc2xhcyBHb21lcyxMYXR5ciBOSUFO"
        "RyxBZmZpY2hlICsgZGlmZnVzaW9uIGRlIGwnaW5mb3JtYXRpb24gc3VyIGxlcyByw6lzZWF1eCBkdSBMQVNQQUQgKyBNYWlsY2hp"
        "bXAscHJvZHVjdGlvbiBldCBwb3N0LXByb2R1Y3Rpb24sU3VyIHBsYWNlIChidXJlYXUgZGUgbGEgZGlyZWN0aW9uKSwsLA0KU8Op"
        "bWluYWlyZSxTw6ltaW5haXJlICxHb3V2ZXJuYW5jZSBldCBzb3V2ZXJhaW5ldMOpIHRlY2hub2xvZ2lxdWUgOiBxdWVscyBlbmpl"
        "dXggcG91ciBsZSBkw6l2ZWxvcHBlbWVudCBzcGF0aWFsIGR1IFPDqW7DqWdhbCA/LCwxNC8wNC8yMDI2LDEwOjAwOjAwLDEyOjAw"
        "OjAwLFN0YW5pc2xhcyBHb21lcywsQWZmaWNoZSArIGRpZmZ1c2lvbiBkZSBsJ2luZm9ybWF0aW9uIHN1ciBsZXMgcsOpc2VhdXgg"
        "ZHUgTEFTUEFEICsgTWFpbGNoaW1wLHByb2R1Y3Rpb24gZXQgcG9zdC1wcm9kdWN0aW9uLCxSZXBvcnTDqSDDoCB1bmUgZGF0ZSB1"
        "bHTDqXJpZXVyZSwsDQpDb3VycyBNZWRpdHMsRm9ybWF0aW9uLEwnw6lxdWlwZSDDqWRpdG9yaWFsZSAoQ2VsaW5lIEJhcnRob25u"
        "YXQpLENvdXJzLDE0LzA0LzIwMjYsMTc6MDA6MDAsMTg6MzA6MDAsTWFtYWRvdSBMYW1pbmUgRGlhbmR5LCwsLEVuIGxpZ25lLCws"
        "DQpNdWx0aWxhdMOpcmFsaXNtZSxSw6l1bmlvbixSw6l1bmlvbiBIZWJkb21hZGFpcmUsUsOpdW5pb24gZGUgdHJhdmFpbCwxNS8w"
        "NC8yMDI2LDEwOjAwOjAwLDExOjAwOjAwLEF5cnRvbiBBdWJyeSxFcXVpcGUgZHUgTkFBTSwsLFN1ciBwbGFjZSAoYnVyZWF1IGRl"
        "IGxhIGRpcmVjdGlvbiksLCwNCkNvdXJzIE1lZGl0cyxGb3JtYXRpb24sTCfDqXF1aXBlIMOpZGl0b3JpYWxlIChDZWxpbmUgQmFy"
        "dGhvbm5hdCksQ291cnMsMTcvMDQvMjAyNiwxNzowMDowMCwxODozMDowMCxNYW1hZG91IExhbWluZSBEaWFuZHksLCwsRW4gbGln"
        "bmUsUmVwb3J0w6kgw6AgdW5lIGRhdGUgdWx0w6lyaWV1cmUsLA0KQ291cnMgTWVkaXRzLEZvcm1hdGlvbixEaWdpdGFsIFNraWxs"
        "cyAoTWluYXRhIFNhcnIpLENvdXJzLDE4LzA0LzIwMjYsMTE6MzA6MDAsMTM6MDA6MDAsTWFtYWRvdSBMYW1pbmUgRGlhbmR5LCws"
        "LEVuIGxpZ25lLEZhaXQsLA0KRkFDRS9ISVJBLFPDqW1pbmFpcmUgLCLCqyBQb3V2b2lycyBmw6ltaW5pbnMgZOKAmWhpZXIgw6Ag"
        "YXVqb3VyZOKAmWh1aSA6IAps4oCZQWZyaXF1ZSBtYXRyaWFyY2FsZSDCuyIsU8OpbWluYWlyZSBzdXIgbGVzIHBvdXZvaXJzIGbD"
        "qW1pbmlucyBlbiBBZnJpcXVlLDE4LzA0LzIwMjYsMTY6MDA6MDAsMTg6MDA6MDAsQWRqYSBBbWluYXRhIENpc3PDqSBEaW9wLFBl"
        "bmRhIE1ib3csLCxFbiBsaWduZSxGYWl0LCwNClPDqW1pbmFpcmUsU8OpbWluYWlyZSAsUG91dm9pcnMgZsOpbWluaW5zIGQnaGll"
        "ciDDoCBhdWpvdXJkJ2h1aSA6IGwnQWZyaXF1ZSBtYXRyaWFyY2FsZSxTZW1pbmFpcmUgZG9jdG9yYWxlIGRlIGwnYXhlIHBvbGl0"
        "aXF1ZXMgdGVjaG5vbG9naXF1ZXMgZXQgc291dmVyYWluZXRlLDE4LzA0LzIwMjYsMTY6MDA6MDAsMTg6MDA6MDAsU3RhbmlzbGFz"
        "IEdvbWVzLFByIFBlbmRhIE1ib3csLEVucmVnaXN0cmVtZW50IGV0IGRpZmZ1c2lvbiBkZSBsYSBzw6lhbmNlLCwsLA0KQ291cnMg"
        "TWVkaXRzLEZvcm1hdGlvbizDiXZhbHVhdGlvbiBldCBpbnTDqWdyaXTDqSBzY2llbnRpZmlxdWUgKFByIFNhcmEgTWVqZG91Ymkp"
        "LENvdXJzLDIwLzA0LzIwMjYsMTc6MDA6MDAsLE1hbWFkb3UgTGFtaW5lIERpYW5keSwsLCxFbiBsaWduZSxGYWl0LCwNCk11bHRp"
        "bGF0w6lyYWxpc21lLFPDqW1pbmFpcmUgLFPDqWFuY2UgZGUgc8OpbWluYWlyZSBOQUFNLFRow6htZTogTGVzIEV0YXRzIGFmcmlj"
        "YWlucyBkYW5zIGxlcyBuw6lnb2NpYXRpb25zIGludGVybmF0aW9uYWxlcywyMi8wNC8yMDI2LDE1OjAwOjAwLDE3OjAwOjAwLEF5"
        "cnRvbiBBdWJyeSxEciBMw6lvbmFyZCBNYXRhbGEtVGFsYSxBZmZpY2hlICsgZGlmZnVzaW9uIGRlIGwnaW5mb3JtYXRpb24gc3Vy"
        "IGxlcyByw6lzZWF1eCBkdSBMQVNQQUQgKyBNYWlsY2hpbXAsRW5yZWdpc3RyZW1lbnQgZXQgZGlmZnVzaW9uIGRlIGxhIHPDqWFu"
        "Y2UsRW4gbGlnbmUsUmVwb3J0w6llIGF1IDYgbWFpIDIwMjUsLA0KLCxUcnVzdCBBZnJpY2EsUmV1bmlvbiAsMjIvMDQvMjAyNiwx"
        "NTozMDowMCwxNjowMDowMCwsLCwsLCwsDQpDb3VycyBNZWRpdHMsRm9ybWF0aW9uLEluaXRpYXRpb24gw6AgbGEgcHJvbW90aW9u"
        "IGV0IMOgIGxhIGRpZmZ1c2lvbiAoSG9jaW5lIENoZWhhYiksQ291cnMsMjIvMDQvMjAyNiwxNjowMDowMCwxNzozMDowMCxNYW1h"
        "ZG91IExhbWluZSBEaWFuZHksLCwsRW4gbGlnbmUsLCwNCkNvdXJzIE1lZGl0cyxGb3JtYXRpb24sSW5pdGlhdGlvbiDDoCBsYSBw"
        "cm9tb3Rpb24gZXQgw6AgbGEgZGlmZnVzaW9uIChIb2NpbmUgQ2hlaGFiKSxDb3VycywyMy8wNC8yMDI2LDE2OjAwOjAwLDE3OjMw"
        "OjAwLE1hbWFkb3UgTGFtaW5lIERpYW5keSwsLCxFbiBsaWduZSwsLA0KTXVsdGlsYXTDqXJhbGlzbWUsVG91cm5hZ2UsVG91cm5h"
        "Z2UgZCd1bmUgY2Fwc3VsZSxUb3VybmFnZSBkJ3VuZSBjYXBzdWxlLDI0LzA0LzIwMjYsMTA6MDA6MDAsMTI6MDA6MDAsRmFkaWxv"
        "dSBOZG95ZSwsLFByw6lzZW5jZSBkJ3VuIG1lbWJyZSBkZSBsJ8OpcXVpcGUgYXVkaW92aXN1ZWxsZSBwb3VyIHRvdXJuYWdlLFN1"
        "ciBwbGFjZSwsLA0KQ291cnMgTWVkaXRzLEZvcm1hdGlvbizDiXZhbHVhdGlvbiBldCBpbnTDqWdyaXTDqSBzY2llbnRpZmlxdWUg"
        "KFByIFNhcmEgTWVqZG91YmkpLENvdXJzLDI0LzA0LzIwMjYsMTc6MDA6MDAsLE1hbWFkb3UgTGFtaW5lIERpYW5keSwsLCxFbiBs"
        "aWduZSxyZXBvcnTDqWUgYXUgMTEgbWFpLCwNClPDqW1pbmFpcmUsU8OpbWluYWlyZSAsIkxlcyDDqWxpdGVzIG9jY2lkZW50YWxl"
        "cyBmYWNlIGF1eCBCUklDUyA6IGVudHJlIGTDqW5pLCBjdXJpb3NpdMOpIGV0IGTDqWZpICIsU8OpbWluYWlyZSwyNS8wNC8yMDI2"
        "LDEwOjAwOjAwLDEyOjAwOjAwLE91c3NleW5vdSBHdWV5ZSxNYXR0aGlldSBHcmFucGllcnJvbixBZmZpY2hlICsgZGlmZnVzaW9u"
        "IGRlIGwnaW5mb3JtYXRpb24gc3VyIGxlcyByw6lzZWF1eCBkdSBMQVNQQUQgKyBNYWlsY2hpbXAgKyBsaWVuIHpvb20sRW5yZWdp"
        "c3RyZW1lbnQgZXQgZGlmZnVzaW9uIGRlIGxhIHPDqWFuY2UsRW4gbGlnbmUsLCwxMDAgMDAwDQpTw6ltaW5haXJlLFPDqW1pbmFp"
        "cmUgLCxTw6ltaW5haXJlLDI1LzA0LzIwMjYsMTU6MzA6MDAsMTc6MzA6MDAsLCwsLCwsLA0KQ291cnMgTWVkaXRzLEZvcm1hdGlv"
        "bizDiXZhbHVhdGlvbiBldCBpbnTDqWdyaXTDqSBzY2llbnRpZmlxdWUgKFByIFNhcmEgTWVqZG91YmkpLENvdXJzLDI3LzA0LzIw"
        "MjYsMTc6MDA6MDAsLE1hbWFkb3UgTGFtaW5lIERpYW5keSwsLCxFbiBsaWduZSwsLA0KR2xvYmFsIEFmcmljYSxUdXRvcmF0LEFj"
        "Y29tcGFnbmVtZW50IEdsb2JhbCBBZnJpY2EgSnVuaW9yLFR1dG9yYXQgYXZlYyBBYmRvdXJhaG1hbmUgQmEsMjgvMDQvMjAyNiww"
        "OTowMDowMCwxMDowMDowMCxBeXJ0b24gQXVicnksQWJkb3VyYWhtYW5lIEJhLCwsU3VyIHBsYWNlLCwsDQpDb3VycyBNZWRpdHMs"
        "Rm9ybWF0aW9uLEluaXRpYXRpb24gw6AgbGEgcHJvbW90aW9uIGV0IMOgIGxhIGRpZmZ1c2lvbiAoSG9jaW5lIENoZWhhYiksQ291"
        "cnMsMjgvMDQvMjAyNiwxNjowMDowMCwxNzozMDowMCxNYW1hZG91IExhbWluZSBEaWFuZHksLCwsRW4gbGlnbmUsLCwNCk11bHRp"
        "bGF0w6lyYWxpc21lLFLDqXVuaW9uLFLDqXVuaW9uIGhlYmRvbWFkYWlyZSBkZSB0cmF2YWlsIGRlIGwnw6lxdWlwZSBOQUFNLFLD"
        "qXVuaW9uIGRlIHRyYXZhaWwsMjkvMDQvMjAyNiwxMDowMDowMCwxMTowMDowMCxBeXJ0b24gQXVicnksLCwsU3VyIHBsYWNlLCws"
        "DQosLFRydXN0IEFmcmljYSxSZXVuaW9uICwyOS8wNC8yMDI2LDE1OjMwOjAwLDE2OjAwOjAwLCwsLCxFbiBsaWduZSwsLA0KQ291"
        "cnMgTWVkaXRzLEZvcm1hdGlvbizDiXZhbHVhdGlvbiBldCBpbnTDqWdyaXTDqSBzY2llbnRpZmlxdWUgKFByIFNhcmEgTWVqZG91"
        "YmkpLENvdXJzLDI5LzA0LzIwMjYsMTc6MDA6MDAsLE1hbWFkb3UgTGFtaW5lIERpYW5keSwsLCxFbiBsaWduZSxyZXBvcnTDqSBh"
        "dSAxNCBtYWksLA0KQXhlIFBUUyxTw6ltaW5haXJlICxJbnRlbGxpZ2VuY2UgYXJ0aWZpY2llbGxlIGV0IGFzc3VyYW5jZSBkZSBs"
        "YSBzw6ljdXJpdMOpIGRlcyBzeXN0w6htZXMgYcOpcm9zcGF0aWF1eCBkZSBub3V2ZWxsZSBnw6luw6lyYXRpb24gPyxTw6ltaW5h"
        "aXJlLDMwLzA0LzIwMjYsMTQ6MDA6MDAsMTU6MzA6MDAsLCwsLCwsLA0KQ291cnMgTWVkaXRzLEZvcm1hdGlvbixJbml0aWF0aW9u"
        "IMOgIGxhIHByb21vdGlvbiBldCDDoCBsYSBkaWZmdXNpb24gKEhvY2luZSBDaGVoYWIpLENvdXJzLDMwLzA0LzIwMjYsMTc6MDA6"
        "MDAsMTg6MzA6MDAsTWFtYWRvdSBMYW1pbmUgRGlhbmR5LCwsLEVuIGxpZ25lLCwsDQpDb3VycyBNZWRpdHMsLCwsLCwsLCwsLCws"
        "LA0KQ291cnMgTWVkaXRzLCwsLCwsLCwsLCwsLCwNCkNvdXJzIE1lZGl0cywsLCwsLCwsLCwsLCws"
)


def _pdate(s):
    s = (s or "").strip()
    for f in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


def _ptime(s):
    s = (s or "").strip()
    for f in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.datetime.strptime(s, f).time()
        except ValueError:
            pass
    return None


def _status(raw):
    r = (raw or "").strip().lower()
    if "annul" in r:
        return "annule"
    if "report" in r:
        return "reporte"
    if "fait" in r:
        return "fait"
    return "a_venir"


def load_events(apps, schema_editor):
    LabEvent = apps.get_model("planning", "LabEvent")
    # garde-fou : ne pas ré-importer si déjà fait
    if LabEvent.objects.filter(created_by="import@laspad.org").exists():
        return

    raw = base64.b64decode("".join(CSV_B64.split())).decode("utf-8", "replace")
    rows = list(csv.reader(io.StringIO(raw)))
    for row in rows[1:]:
        if not any(c.strip() for c in row):
            continue
        row = row + [""] * (15 - len(row))
        (projet, type_e, titre, desc, d1, heure, d2, resp, invites,
         bcom, bprod, lieu, statut_raw, _x, budget) = row[:15]
        titre = titre.strip()
        dd = _pdate(d1)
        if not titre or not dd:
            continue
        LabEvent.objects.create(
            projet=projet.strip(), type_event=(type_e.strip() or "Autre"),
            titre=titre, description=desc.strip(), date_debut=dd,
            heure=_ptime(heure), date_fin=_pdate(d2), responsable=resp.strip(),
            invites=invites.strip(), besoins_com=bcom.strip(),
            besoins_prod=bprod.strip(), lieu=lieu.strip(),
            statut=_status(statut_raw), budget=budget.strip(),
            created_by="import@laspad.org",
        )


def unload_events(apps, schema_editor):
    LabEvent = apps.get_model("planning", "LabEvent")
    LabEvent.objects.filter(created_by="import@laspad.org").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("planning", "0004_fix_member_names"),
    ]

    operations = [
        migrations.RunPython(load_events, unload_events),
    ]
