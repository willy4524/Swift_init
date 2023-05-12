# 引入 requests 模組
import requests
import os
def checkver():
    v1 = '1.0.11'

    # 使用 GET 方式下載普通網頁
    r = requests.get('https://www.pingtex.tw/api/sys/firmwareversion?deviceGuid=TS10G-0000000&appOS=1&appVersion=4.0.1&countryCode=CN')

    print(r.status_code)
    if r.status_code == requests.codes.ok:
        print("OK")
        data = r.json()
        print(data)
        print(data['status'])
        v2 = data['firmwareVersion']
        t1 = tuple(int(val) for val in v1.split('.'))
        t2 = tuple(int(val) for val in v2.split('.'))
        print(t1, t2)
        if t2 > t1:
            r = requests.get('https://www.pingtex.tw/api/sys/firmwaredownloadurl?firmwareGuid=0d67bd94-1493-ed11-8c1a-00155d070900&firmwareVersion=1.0.13&deviceGuid=TS10G-0000000&appOS=1&appVersion=4.0.1&countryCode=CN')
            print(r.status_code)
            if r.status_code == requests.codes.ok:
                print("OK")
                data = r.json()
                nxpbinURL = data['hyperLinkNXP']
                espbinURL = data['hyperLinkESP']
                AudiobinURL = data['hyperLinkAudio']
                print(nxpbinURL)
                print(espbinURL)
                print(AudiobinURL)
                r = requests.get(nxpbinURL, stream=True)
                with open('nxp_bin/main_nxp.bin', 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)
                print(r.status_code)
                if r.status_code != requests.codes.ok:
                    return -1
                r = requests.get(espbinURL, stream=True)
                with open('esp_bin/0x10000-main.bin', 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)
                print(r.status_code)
                if r.status_code != requests.codes.ok:
                    return -1
                r = requests.get(AudiobinURL, stream=True)
                with open('esp_bin/0x810000-audio.bin', 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)
                print(r.status_code)
                if r.status_code != requests.codes.ok:
                    return -1

checkver()