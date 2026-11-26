import time
from smartcard.System import readers
from smartcard.util import toBytes, toHexString

CHIP_SIZES = {
    'Otomatik Algıla (Önerilen)': None,
    'NTAG213 (144 Bayt)': 144,
    'NTAG215 (504 Bayt)': 504,
    'NTAG216 (888 Bayt)': 888,
    'NTAG210 / NTAG212': 48,
    'MIFARE Ultralight / Ultralight C / EV1': 48,
    'MIFARE Classic 1K / 4K': 1024
}

class NFCWriter:
    def __init__(self):
        self.reader = None
        self.conn = None
        self.mode = None

    def connect_pn532(self, port):
        try:
            import serial
            self.ser = serial.Serial(port, 115200, timeout=1)
            # PN532 WakeUp komutu
            self.ser.write(b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            time.sleep(0.1)
            self.ser.reset_input_buffer()
            self.mode = 'pn532'
            return True, f'PN532 {port} portuna bağlandı.'
        except Exception as e:
            return False, f'PN532 bağlantı hatası: {str(e)}'

    def connect_acr122u(self):
        try:
            r = readers()
            if not r:
                return False, 'ACR122U okuyucu bulunamadı. Lütfen sürücüleri ve bağlantıyı kontrol edin.'
            self.reader = r[0]
            self.conn = self.reader.createConnection()
            self.conn.connect()
            self.mode = 'acr122u'
            return True, 'ACR122U bağlandı.'
        except Exception as e:
            return False, f'ACR122U bağlantı hatası: {str(e)}'

    def wait_for_card(self):
        if self.mode == 'acr122u':
            try:
                # ACR122U UID Okuma APDU'su
                data, sw1, sw2 = self.conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                if sw1 == 0x90 and sw2 == 0x00:
                    uid = toHexString(data).replace(' ', '')
                    return uid
            except Exception:
                pass
            return None
        
        elif self.mode == 'pn532':
            # PN532 InListPassiveTarget (Kart ara)
            cmd = b'\x00\x00\xff\x04\xfc\xd4\x4a\x01\x00\xe1\x00'
            self.ser.write(cmd)
            resp = self.ser.read(20)
            if b'\xd5\x4b' in resp:
                # UID'yi paketten ayıkla (Basit bir parse)
                idx = resp.find(b'\xd5\x4b')
                if idx != -1 and len(resp) > idx + 8:
                    uid_bytes = resp[idx+7:idx+11]
                    return toHexString(list(uid_bytes)).replace(' ', '')
            return None
        return None

    def write_ndef_url(self, url, chip_type='Otomatik Algıla (Önerilen)'):
        if not url: return False, 'URL boş olamaz.'
        
        # NDEF URI kaydı oluşturma (https:// için prefix 04 kullanılır)
        prefix = 0x04 
        url_rest = url.replace('https://', '')
        url_bytes = list(url_rest.encode('utf-8'))
        
        # TLV Paketi: 03 [Uzunluk] D1 01 [NDEF_Uzunluk] 55 04 [URL_Byte...] FE
        ndef_payload = [0xD1, 0x01, len(url_bytes) + 1, 0x55, prefix] + url_bytes
        tlv = [0x03, len(ndef_payload)] + ndef_payload + [0xFE]
        
        # 4 byte'lık sayfalara tamamla
        while len(tlv) % 4 != 0:
            tlv.append(0x00)

        try:
            if self.mode == 'acr122u':
                # NTAG Sayfa yazma (Sayfa 4'ten başlar)
                page = 4
                for i in range(0, len(tlv), 4):
                    chunk = tlv[i:i+4]
                    # ACR122U Update Binary APDU
                    apdu = [0xFF, 0xD6, 0x00, page, 0x04] + chunk
                    data, sw1, sw2 = self.conn.transmit(apdu)
                    if sw1 != 0x90:
                        return False, f'Yazma hatası (Sayfa {page})'
                    page += 1
                return True, 'NDEF başarıyla yazıldı.'

            elif self.mode == 'pn532':
                # PN532 InDataExchange (A2 = WRITE komutu)
                page = 4
                for i in range(0, len(tlv), 4):
                    chunk = tlv[i:i+4]
                    # A2 [page] [data]
                    payload = [0xA2, page] + chunk
                    length = len(payload)
                    lcs = (~length + 1) & 0xFF
                    tfi = 0xD4
                    dcs = (~(tfi + 0x40 + 0x01 + sum(payload)) + 1) & 0xFF
                    
                    frame = [0x00, 0x00, 0xFF, length, lcs, tfi, 0x40, 0x01] + payload + [dcs, 0x00]
                    self.ser.write(bytes(frame))
                    resp = self.ser.read(20)
                    if b'\xd5\x41\x00' not in resp: # 00 = Başarılı
                        return False, f'PN532 Yazma hatası (Sayfa {page})'
                    page += 1
                return True, 'NDEF başarıyla yazıldı.'
        except Exception as e:
            return False, f'Donanım yazma hatası: {str(e)}'

        return False, 'Bağlı okuyucu yok.'

    def read_ndef_url(self):
        try:
            if self.mode == 'acr122u':
                # NDEF okumak için ilk sayfaları oku
                apdu = [0xFF, 0xB0, 0x00, 0x04, 0x10] # 16 byte oku
                data, sw1, sw2 = self.conn.transmit(apdu)
                if sw1 == 0x90:
                    # Basit NDEF parse (03 [len] D1 01 [len] 55 04 ...)
                    if data[0] == 0x03:
                        ndef_len = data[1]
                        url_bytes = data[5:5+ndef_len-1]
                        url = 'https://' + bytes(url_bytes).decode('utf-8', errors='ignore')
                        return True, url
                return False, 'NDEF verisi okunamadı.'

            elif self.mode == 'pn532':
                # PN532 InDataExchange (30 = READ)
                payload = [0x30, 0x04]
                length = len(payload)
                lcs = (~length + 1) & 0xFF
                tfi = 0xD4
                dcs = (~(tfi + 0x40 + 0x01 + sum(payload)) + 1) & 0xFF
                frame = [0x00, 0x00, 0xFF, length, lcs, tfi, 0x40, 0x01] + payload + [dcs, 0x00]
                self.ser.write(bytes(frame))
                resp = self.ser.read(30)
                if b'\xd5\x41\x00' in resp:
                    # Basit parse
                    idx = resp.find(b'\xd5\x41\x00')
                    if idx != -1:
                        raw = resp[idx+3:]
                        if len(raw) > 6 and raw[0] == 0x03:
                            url_bytes = raw[5:5+raw[1]-1]
                            url = 'https://' + bytes(url_bytes).decode('utf-8', errors='ignore')
                            return True, url
                return False, 'NDEF verisi okunamadı.'
        except Exception as e:
            return False, f'Okuma hatası: {str(e)}'
        return False, 'Bağlı okuyucu yok.'

    def lock_card(self):
        if self.mode == 'acr122u':
            try:
                # NTAG213/215/216 Statik Kilit (Static Lock Bytes) sayfa 2'yi yaz.
                # 0xFF 0xFF ile kilitlenir (Geri dönüşü yoktur)
                apdu = [0xFF, 0xD6, 0x00, 0x02, 0x04, 0xFF, 0xFF, 0xFF, 0xFF]
                data, sw1, sw2 = self.conn.transmit(apdu)
                if sw1 == 0x90:
                    return True, 'Kart kalıcı olarak kilitlendi.'
                return False, 'Kilit yazma reddedildi.'
            except Exception as e:
                return False, f'Kilit hatası: {str(e)}'
        elif self.mode == 'pn532':
            try:
                payload = [0xA2, 0x02, 0xFF, 0xFF, 0xFF, 0xFF]
                length = len(payload)
                lcs = (~length + 1) & 0xFF
                tfi = 0xD4
                dcs = (~(tfi + 0x40 + 0x01 + sum(payload)) + 1) & 0xFF
                frame = [0x00, 0x00, 0xFF, length, lcs, tfi, 0x40, 0x01] + payload + [dcs, 0x00]
                self.ser.write(bytes(frame))
                resp = self.ser.read(20)
                if b'\xd5\x41\x00' in resp:
                    return True, 'Kart kalıcı olarak kilitlendi.'
                return False, 'Kilit yazma reddedildi.'
            except Exception as e:
                return False, f'Kilit hatası: {str(e)}'
        return False, 'Bağlı okuyucu yok.'
