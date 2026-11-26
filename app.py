import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading, winsound, os, webbrowser
from database import (init_db, get_setting, set_setting, find_by_uid,
                      insert_card, get_next_card_id, get_all_cards)
from routes_generator import generate_routes
from nfc_writer import NFCWriter, CHIP_SIZES

CARD_TYPES = ['Çoklu IBAN Kartı', 'Dijital Menü', 'Google Yorum',
              'Instagram', 'WhatsApp', 'Sahibinden Mağaza', 'Özel Bağlantı']
BANKS = ['Akbank', 'Garanti BBVA', 'Ziraat Bankası', 'İş Bankası',
         'Yapı Kredi', 'QNB', 'VakıfBank', 'Halkbank', 'Enpara',
         'Kuveyt Türk', 'Diğer']
BANK_COLORS = {'Akbank': '#E30613', 'Garanti BBVA': '#009B4E',
               'Ziraat Bankası': '#E30613', 'İş Bankası': '#004B93',
               'Yapı Kredi': '#002B5C', 'QNB': '#5D2E8C',
               'VakıfBank': '#FEC50C', 'Halkbank': '#004A99',
               'Enpara': '#00A0E3', 'Kuveyt Türk': '#00A651',
               'Diğer': '#666666'}
READER_MODES = ['Simülasyon / Test Modu', 'PN532 (UART/HSU)', 'ACS ACR122U (PC/SC)']


def _now():
    from datetime import datetime
    d = datetime.now()
    return '{:02d}:{:02d}:{:02d}'.format(d.hour, d.minute, d.second)


class NFCApp:
    def __init__(self, root):
        self.root = root
        self.root.title('NFC Kart Sabit Kapı ve Yönlendirme Yönetim Sistemi')
        self.root.geometry('1220x820')
        self.writer = NFCWriter(mode='simulation')
        self.iban_rows = []
        self.single_fields = {}
        self.total_count = tk.IntVar(value=10)
        self.current_index = tk.IntVar(value=0)
        self.group_id_var = tk.StringVar()
        self.last_uid = None

        init_db()
        if not get_setting('gate_url'):
            set_setting('gate_url', 'https://isma-sketch.github.io/g/?id=')
        if not get_setting('reader_mode'):
            set_setting('reader_mode', 'Simülasyon / Test Modu')
        if not get_setting('chip_type'):
            set_setting('chip_type', 'Otomatik Algıla (Önerilen)')
        if not get_setting('lock_card'):
            set_setting('lock_card', '0')

        self.build_ui()
        self.log('Sistem hazır. Okuyucu modu: Simülasyon / Test Modu')
        self.log('Sabit kapı URL: ' + get_setting('gate_url'))

    def build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill='x')

        ttk.Label(top, text='Sabit Kapı URL:').grid(row=0, column=0, sticky='w')
        self.gate_entry = ttk.Entry(top, width=60)
        self.gate_entry.insert(0, get_setting('gate_url'))
        self.gate_entry.grid(row=0, column=1, sticky='we', padx=4)
        ttk.Button(top, text='Kaydet', command=self.save_gate).grid(row=0, column=2, padx=2)
        ttk.Button(top, text='Önizleme', command=self.open_preview).grid(row=0, column=3, padx=2)

        ttk.Label(top, text='Okuyucu:').grid(row=1, column=0, sticky='w', pady=4)
        self.reader_var = tk.StringVar(value=get_setting('reader_mode'))
        ttk.Combobox(top, textvariable=self.reader_var, values=READER_MODES,
                     width=30, state='readonly').grid(row=1, column=1, sticky='w', padx=4)
        ttk.Button(top, text='Bağlan', command=self.connect_reader).grid(row=1, column=2, padx=2)

        ttk.Label(top, text='Çip Türü:').grid(row=2, column=0, sticky='w')
        self.chip_var = tk.StringVar(value=get_setting('chip_type'))
        ttk.Combobox(top, textvariable=self.chip_var, values=list(CHIP_SIZES.keys()),
                     width=45, state='readonly').grid(row=2, column=1, sticky='w', padx=4)

        ttk.Label(top, text='Kart Türü:').grid(row=3, column=0, sticky='w', pady=4)
        self.type_var = tk.StringVar(value=CARD_TYPES[0])
        type_combo = ttk.Combobox(top, textvariable=self.type_var, values=CARD_TYPES,
                                  width=30, state='readonly')
        type_combo.grid(row=3, column=1, sticky='w', padx=4)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.on_type_change())

        self.lock_var = tk.BooleanVar(value=get_setting('lock_card') == '1')
        ttk.Checkbutton(top, text='Kalıcı Kilit Vur (salt-okunur)',
                        variable=self.lock_var).grid(row=3, column=2, columnspan=2, sticky='w')

        ttk.Label(top, text='Grup ID:').grid(row=4, column=0, sticky='w')
        ttk.Entry(top, textvariable=self.group_id_var, width=20).grid(row=4, column=1, sticky='w', padx=4)

        ttk.Label(top, text='Toplam Kart (Grup):').grid(row=4, column=2, sticky='e')
        ttk.Spinbox(top, from_=1, to=1000, textvariable=self.total_count, width=8).grid(row=4, column=3, sticky='w')

        self.mode_var = tk.StringVar(value='tekil')
        mode_frame = ttk.Frame(top)
        mode_frame.grid(row=5, column=0, columnspan=4, sticky='w', pady=4)
        ttk.Radiobutton(mode_frame, text='Tekil Mod', variable=self.mode_var,
                        value='tekil').pack(side='left', padx=4)
        ttk.Radiobutton(mode_frame, text='Gruplu Mod', variable=self.mode_var,
                        value='gruplu').pack(side='left', padx=4)
        ttk.Label(mode_frame, text='Sayaç:').pack(side='left', padx=(20, 4))
        self.counter_label = ttk.Label(mode_frame, text='0 / 0')
        self.counter_label.pack(side='left')

        mid = ttk.PanedWindow(self.root, orient='horizontal')
        mid.pack(fill='both', expand=True, padx=8, pady=4)

        left = ttk.Frame(mid, padding=6)
        mid.add(left, weight=3)
        self.dynamic_frame = ttk.LabelFrame(left, text='Kart İçeriği', padding=6)
        self.dynamic_frame.pack(fill='both', expand=True)
        self.iban_container = ttk.Frame(self.dynamic_frame)
        self.iban_container.pack(fill='both', expand=True)

        right = ttk.Frame(mid, padding=6)
        mid.add(right, weight=2)
        ttk.Label(right, text='Durum Günlüğü').pack(anchor='w')
        self.log_text = tk.Text(right, height=20, state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True, pady=4)

        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill='x')
        ttk.Button(bottom, text='Kartı Yaz / Doğrula / Kilitle / Kaydet',
                   command=self.process_card).pack(side='left', padx=4)
        ttk.Button(bottom, text='routes.json Yenile',
                   command=self.refresh_routes).pack(side='left', padx=4)

        self.on_type_change()

    def on_type_change(self):
        for w in self.dynamic_frame.winfo_children():
            if w is not self.iban_container:
                w.destroy()
        for w in self.iban_container.winfo_children():
            w.destroy()
        self.iban_rows = []
        self.single_fields = {}
        t = self.type_var.get()
        if t == 'Çoklu IBAN Kartı':
            self.build_iban_form()
        else:
            self.build_single_form(t)

    def build_iban_form(self):
        ttk.Label(self.iban_container, text='Kart Başlığı:').grid(row=0, column=0, sticky='w')
        self.card_title = tk.StringVar(value='Banka Hesaplarım')
        ttk.Entry(self.iban_container, textvariable=self.card_title,
                  width=40).grid(row=0, column=1, columnspan=4, sticky='we', pady=2)
        ttk.Button(self.iban_container, text='+ Hesap Ekle',
                   command=self.add_iban_row).grid(row=1, column=0, pady=4)
        self.iban_list_frame = ttk.Frame(self.iban_container)
        self.iban_list_frame.grid(row=2, column=0, columnspan=5, sticky='nsew')

    def add_iban_row(self):
        row_frame = ttk.Frame(self.iban_list_frame)
        row_frame.pack(fill='x', pady=2)
        bank_var = tk.StringVar(value='Akbank')
        title_var = tk.StringVar()
        name_var = tk.StringVar()
        iban_var = tk.StringVar()
        ttk.Label(row_frame, text='Banka:').pack(side='left')
        ttk.Combobox(row_frame, textvariable=bank_var, values=BANKS, width=13,
                     state='readonly').pack(side='left', padx=2)
        ttk.Label(row_frame, text='Hesap:').pack(side='left')
        ttk.Entry(row_frame, textvariable=title_var, width=12).pack(side='left', padx=2)
        ttk.Label(row_frame, text='Alıcı:').pack(side='left')
        ttk.Entry(row_frame, textvariable=name_var, width=14).pack(side='left', padx=2)
        ttk.Label(row_frame, text='IBAN:').pack(side='left')
        ttk.Entry(row_frame, textvariable=iban_var, width=24).pack(side='left', padx=2)
        data = {'frame': row_frame, 'bank': bank_var, 'title': title_var,
                'name': name_var, 'iban': iban_var}
        def remove():
            row_frame.destroy()
            self.iban_rows.remove(data)
        ttk.Button(row_frame, text='X', width=3, command=remove).pack(side='left', padx=2)
        self.iban_rows.append(data)

    def build_single_form(self, t):
        if t == 'Dijital Menü':
            self._field('Başlık:', 'title'); self._field('Menü URL:', 'url', 50)
        elif t == 'Google Yorum':
            self._field('İşletme Adı:', 'title'); self._field('Google Yorum URL:', 'url', 50)
        elif t == 'Instagram':
            self._field('Kullanıcı Adı:', 'username'); self._field('Instagram URL:', 'url', 50)
        elif t == 'WhatsApp':
            self._field('İsim:', 'title'); self._field('Telefon (905xx...):', 'phone')
            self._field('WhatsApp URL:', 'url', 50)
        elif t == 'Sahibinden Mağaza':
            self._field('Mağaza Adı:', 'title'); self._field('Mağaza URL:', 'url', 50)
        elif t == 'Özel Bağlantı':
            self._field('Başlık:', 'title'); self._field('Hedef URL:', 'url', 50)

    def _field(self, label, key, width=40):
        row = ttk.Frame(self.dynamic_frame)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text=label, width=18).pack(side='left')
        var = tk.StringVar()
        ttk.Entry(row, textvariable=var, width=width).pack(side='left', fill='x', expand=True)
        self.single_fields[key] = var

    def save_gate(self):
        set_setting('gate_url', self.gate_entry.get().strip())
        set_setting('reader_mode', self.reader_var.get())
        set_setting('chip_type', self.chip_var.get())
        set_setting('lock_card', '1' if self.lock_var.get() else '0')
        self.log('Ayarlar kaydedildi.')

    def connect_reader(self):
        mode = self.reader_var.get()
        if mode == 'Simülasyon / Test Modu':
            self.writer.set_mode('simulation')
            self.log('Simülasyon modu aktif.')
            return
        if mode == 'PN532 (UART/HSU)':
            port = simpledialog.askstring('COM Port', 'COM port girin (ör. COM3):')
            if port:
                ok, msg = self.writer.connect_pn532(port)
                self.log(msg)
            return
        if mode == 'ACS ACR122U (PC/SC)':
            ok, msg = self.writer.connect_acr122u()
            self.log(msg)
            return

    def log(self, m):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', '[' + _now() + '] ' + m + '\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def collect_data(self):
        t = self.type_var.get()
        if t == 'Çoklu IBAN Kartı':
            accs = []
            for r in self.iban_rows:
                iban = r['iban'].get().strip()
                if not iban:
                    continue
                bank = r['bank'].get()
                accs.append({'bank_name': bank,
                             'bank_color': BANK_COLORS.get(bank, '#666666'),
                             'account_title': r['title'].get().strip(),
                             'recipient': r['name'].get().strip(),
                             'iban': iban})
            if not accs:
                return None, 'En az bir IBAN ekleyin'
            return {'title': self.card_title.get().strip() or 'Banka Hesaplarım',
                    'accounts': accs}, None
        data = {}
        for k, v in self.single_fields.items():
            val = v.get().strip()
            if not val:
                return None, 'Alan boş: ' + k
            data[k] = val
        return data, None

    def refresh_routes(self):
        try:
            path = generate_routes()
            self.log('routes.json güncellendi: ' + path)
        except Exception as e:
            self.log('Hata: ' + str(e))

    def process_card(self):
        threading.Thread(target=self._process_card_thread, daemon=True).start()

    def _ask_yesno(self, title, msg):
        result = {'ans': False}
        evt = threading.Event()
        def prompt():
            result['ans'] = messagebox.askyesno(title, msg)
            evt.set()
        self.root.after(0, prompt)
        evt.wait()
        return result['ans']

    def _process_card_thread(self):
        try:
            data, err = self.collect_data()
            if err:
                self.log('HATA: ' + err); return

            gate = get_setting('gate_url')
            group_id = self.group_id_var.get().strip()
            if not group_id:
                group_id = 'G' + _now().replace(':', '')

            if self.mode_var.get() == 'tekil':
                card_id = 'K' + _now().replace(':', '') + str(len(get_all_cards()) + 1).zfill(3)
                total = 1; idx = 1
            else:
                card_id = get_next_card_id(group_id)
                total = self.total_count.get()
                idx = self.current_index.get() + 1
                if idx > total:
                    self.log('Bu grup için toplam karta ulaşıldı. Yeni grup ID girin.')
                    return

            self.log('Kart okutun (UID bekleniyor)...')
            uid = self.writer.wait_for_card(timeout=30)
            if not uid:
                self.log('UID okunamadı.'); return
            self.last_uid = uid
            self.log('UID: ' + uid)

            existing = find_by_uid(uid)
            if existing:
                ans = self._ask_yesno('Kayıtlı Kart',
                                      'Bu kart (UID) zaten kayıtlı! Üzerine yazılsın mı?')
                if not ans:
                    self.log('Kullanıcı iptal etti.'); return

            target_url = gate + card_id
            self.log('Yazılıyor: ' + target_url)
            ok, msg = self.writer.write_ndef_url(target_url, self.chip_var.get())
            self.log(msg)
            if not ok:
                return

            ok, read_back = self.writer.read_ndef_url()
            if not ok or read_back != target_url:
                self.log('DOĞRULAMA BAŞARISIZ! Kilitleme yapılmadı.')
                return
            self.log('Doğrulama başarılı.')

            if self.lock_var.get():
                ok, msg = self.writer.lock_card()
                self.log(msg)
                if not ok:
                    self.log('UYARI: Kilit uygulanamadı, kayıt devam ediyor.')

            insert_card(card_id, uid, self.type_var.get(), group_id, data, self.lock_var.get())
            self.refresh_routes()
            try:
                winsound.Beep(1200, 150)
            except Exception:
                pass
            self.log('BAŞARILI: Kart kaydedildi (' + card_id + ').')

            if self.mode_var.get() == 'tekil':
                self.root.after(0, self.on_type_change)
                self.log('Form sıfırlandı. Yeni kart girişine hazır.')
            else:
                self.current_index.set(idx)
                self.root.after(0, lambda: self.counter_label.config(
                    text=str(idx) + ' / ' + str(total)))
                self.log('Sayaç: ' + str(idx) + ' / ' + str(total) + '. Sıradaki kartı okutun.')
        except Exception as e:
            self.log('HATA: ' + str(e))

    def open_preview(self):
        p = os.path.abspath('onizleme.html')
        if os.path.exists(p):
            webbrowser.open('file:///' + p.replace('\\', '/'))
        else:
            self.log('onizleme.html bulunamadı.')


def main():
    root = tk.Tk()
    NFCApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
