import time, random

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
    def __init__(self, mode='simulation'):
        self.mode = mode
        self.reader = None
        self._last_url = None
        self._last_uid = None

    def set_mode(self, mode):
        self.mode = mode

    def connect_pn532(self, port):
        try:
            import serial
            self.reader = serial.Serial(port, 115200, timeout=1)
            self.mode = 'pn532'
            return True, 'PN532 bağlandı: ' + port
        except Exception as e:
            return False, 'PN532 bağlanamadı: ' + str(e)

    def connect_acr122u(self):
        try:
            from smartcard.System import readers
            r = readers()
            if not r:
                return False, 'ACR122U okuyucu bulunamadı'
            self.reader = r[0]
            self.mode = 'acr122u'
            return True, 'ACR122U bağlandı'
        except Exception as e:
            return False, 'ACR122U bağlanamadı: ' + str(e)

    def wait_for_card(self, timeout=30):
        if self.mode == 'simulation':
            time.sleep(1.2)
            parts = ['{:02X}'.format(random.randint(0, 255)) for _ in range(6)]
            self._last_uid = '04:' + ':'.join(parts)
            return self._last_uid
        if self.mode == 'acr122u' and self.reader:
            conn = self.reader.createConnection()
            conn.connect()
            data, sw1, sw2 = conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
            if sw1 == 0x90 and sw2 == 0x00:
                self._last_uid = ':'.join('{:02X}'.format(b) for b in data)
                return self._last_uid
        return None

    def write_ndef_url(self, url, chip_type='Otomatik Algıla (Önerilen)'):
        if self.mode == 'simulation':
            time.sleep(0.7)
            self._last_url = url
            return True, 'Simülasyon: NDEF yazıldı'
        return False, 'Gerçek donanım yazma modülü yüklenmedi'

    def read_ndef_url(self):
        if self.mode == 'simulation':
            return True, self._last_url
        return False, None

    def lock_card(self):
        if self.mode == 'simulation':
            time.sleep(0.3)
            return True, 'Simülasyon: Kart kilitlendi'
        return False, 'Kilit desteklenmiyor'
