import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading, winsound, os, webbrowser, json, sqlite3
from database import (init_db, get_setting, set_setting, find_by_uid,
                      insert_card, get_next_card_id, get_all_cards,
                      update_card_data, update_group_data, delete_card)
from routes_generator import generate_routes
from nfc_writer import NFCWriter, CHIP_SIZES

CARD_TYPES = ['Çoklu IBAN Kartı', 'Dijital Menü', 'Google Yorum', 'Instagram', 'WhatsApp', 'Sahibinden Mağaza', 'Özel Bağlantı']
BANKS = ['Akbank', 'Garanti BBVA', 'Ziraat Bankası', 'İş Bankası', 'Yapı Kredi', 'QNB', 'VakıfBank', 'Halkbank', 'Enpara', 'Kuveyt Türk', 'Diğer']
BANK_COLORS = {'Akbank': '#E30613', 'Garanti BBVA': '#009B4E', 'Ziraat Bankası': '#E30613', 'İş Bankası': '#004B93', 'Yapı Kredi': '#002B5C', 'QNB': '#5D2E8C', 'VakıfBank': '#FEC50C', 'Halkbank': '#004A99', 'Enpara': '#00A0E3', 'Kuveyt Türk': '#00A651', 'Diğer': '#666666'}
READER_MODES = ['PN532 (UART/HSU)', 'ACS ACR122U (PC/SC)']

def _now():
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

class NFCApp:
    def __init__(self, root):
        self.root = root
        self.root.title('NFC Yönetim Paneli (Donanım Modu)')
        self.root.geometry('1100x750')
        self.writer = NFCWriter()
        
        self.iban_rows = []
        self.single_fields = {}
        self.total_count = tk.IntVar(value=5)
        self.current_index = tk.IntVar(value=0)
        self.group_id_var = tk.StringVar()
        self.card_owner_var = tk.StringVar()

        init_db()
        self.setup_defaults()
        self.build_ui()
        self.refresh_card_list()

    def setup_defaults(self):
        if not get_setting('gate_url'): set_setting('gate_url', 'https://isma-sketch.github.io/g/?id=')
        if not get_setting('reader_mode'): set_setting('reader_mode', READER_MODES[0])
        if not get_setting('chip_type'): set_setting('chip_type', 'Otomatik Algıla (Önerilen)')
        if not get_setting('lock_card'): set_setting('lock_card', '0')

    def build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.tab_write = ttk.Frame(self.notebook, padding=10)
        self.tab_manage = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_write, text=' Kart Yazma & Donanım ')
        self.notebook.add(self.tab_manage, text=' Kayıtlar ve Grup Yönetimi ')
        
        self.build_write_tab()
        self.build_manage_tab()

    def build_write_tab(self):
        top = ttk.LabelFrame(self.tab_write, text="Sistem Ayarları & Donanım", padding=10)
        top.pack(fill='x', pady=5)
        
        ttk.Label(top, text='Sabit Kapı URL:').grid(row=0, column=0, sticky='w')
        self.gate_entry = ttk.Entry(top, width=50)
        self.gate_entry.insert(0, get_setting('gate_url'))
        self.gate_entry.grid(row=0, column=1, padx=5)
        ttk.Button(top, text='Kaydet', command=self.save_gate).grid(row=0, column=2, padx=5)
        
        ttk.Label(top, text='Okuyucu:').grid(row=1, column=0, sticky='w', pady=5)
        self.reader_var = tk.StringVar(value=get_setting('reader_mode'))
        ttk.Combobox(top, textvariable=self.reader_var, values=READER_MODES, width=25, state='readonly').grid(row=1, column=1, sticky='w', padx=5)
        ttk.Button(top, text='Bağlan', command=self.connect_reader).grid(row=1, column=2, sticky='w', padx=5)

        ttk.Label(top, text='Çip:').grid(row=2, column=0, sticky='w')
        self.chip_var = tk.StringVar(value=get_setting('chip_type'))
        ttk.Combobox(top, textvariable=self.chip_var, values=list(CHIP_SIZES.keys()), width=30, state='readonly').grid(row=2, column=1, sticky='w', padx=5)
        
        mid = ttk.PanedWindow(self.tab_write, orient='horizontal')
        mid.pack(fill='both', expand=True, pady=5)
        
        form_frame = ttk.LabelFrame(mid, text="Kart İçeriği", padding=10)
        mid.add(form_frame, weight=3)
        
        tf = ttk.Frame(form_frame)
        tf.pack(fill='x', pady=5)
        ttk.Label(tf, text='Kart Türü:').pack(side='left')
        self.type_var = tk.StringVar(value=CARD_TYPES[0])
        cb = ttk.Combobox(tf, textvariable=self.type_var, values=CARD_TYPES, width=25, state='readonly')
        cb.pack(side='left', padx=5)
        cb.bind('<<ComboboxSelected>>', lambda e: self.on_type_change())
        
        self.lock_var = tk.BooleanVar(value=get_setting('lock_card') == '1')
        ttk.Checkbutton(tf, text='Kalıcı Kilit Vur', variable=self.lock_var).pack(side='left', padx=15)
        
        gf = ttk.Frame(form_frame)
        gf.pack(fill='x', pady=5)
        self.mode_var = tk.StringVar(value='tekil')
        ttk.Radiobutton(gf, text='Tekil', variable=self.mode_var, value='tekil').pack(side='left')
        ttk.Radiobutton(gf, text='Gruplu', variable=self.mode_var, value='gruplu').pack(side='left', padx=10)
        ttk.Label(gf, text='Grup ID:').pack(side='left', padx=5)
        ttk.Entry(gf, textvariable=self.group_id_var, width=15).pack(side='left')
        ttk.Label(gf, text='Toplam:').pack(side='left', padx=5)
        ttk.Spinbox(gf, from_=1, to=100, textvariable=self.total_count, width=5).pack(side='left')
        self.counter_label = ttk.Label(gf, text='0 / 0', foreground='blue')
        self.counter_label.pack(side='left', padx=10)

        self.dynamic_frame = ttk.Frame(form_frame)
        self.dynamic_frame.pack(fill='both', expand=True, pady=10)
        self.iban_container = ttk.Frame(self.dynamic_frame)
        self.iban_container.pack(fill='both', expand=True)
        
        log_frame = ttk.LabelFrame(mid, text="İşlem Günlüğü", padding=5)
        mid.add(log_frame, weight=2)
        self.log_text = tk.Text(log_frame, state='disabled', wrap='word', bg='#f4f4f4')
        self.log_text.pack(fill='both', expand=True)
        
        bottom = ttk.Frame(self.tab_write)
        bottom.pack(fill='x', pady=5)
        ttk.Button(bottom, text='YAZDIR -> DOĞRULA -> KİLİTLE -> KAYDET', command=self.process_card).pack(side='left', padx=5)
        ttk.Button(bottom, text='JSON Güncelle', command=self.refresh_routes).pack(side='left', padx=5)
        
        self.on_type_change()

    def build_manage_tab(self):
        top = ttk.Frame(self.tab_manage)
        top.pack(fill='x', pady=5)
        ttk.Label(top, text='Ara (ID, UID, Tür):').pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.refresh_card_list())
        ttk.Entry(top, textvariable=self.search_var, width=30).pack(side='left', padx=5)
        ttk.Button(top, text='Listeyi Yenile', command=self.refresh_card_list).pack(side='left', padx=5)
        
        cols = ('ID', 'Tür', 'Grup', 'UID', 'Kilitli')
        self.tree = ttk.Treeview(self.tab_manage, columns=cols, show='headings', height=15)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill='both', expand=True, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        edit_frame = ttk.LabelFrame(self.tab_manage, text="Seçili Kartı Düzenle", padding=10)
        edit_frame.pack(fill='x', pady=5)
        
        ttk.Label(edit_frame, text='Başlık:').grid(row=0, column=0, sticky='w')
        self.edit_title_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.edit_title_var, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(edit_frame, text='JSON İçerik:').grid(row=1, column=0, sticky='w', pady=5)
        self.edit_json_text = tk.Text(edit_frame, height=5, width=60)
        self.edit_json_text.grid(row=1, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text='Bu Kartı Güncelle', command=self.update_selected_card).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Bu GRUBU Güncelle', command=self.update_selected_group).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Kartı SİL', command=self.delete_selected_card).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='GitHub\'a Gönder', command=self.git_push_info).pack(side='right', padx=5)

    def log(self, m):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', f'[{_now()}] {m}\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def refresh_card_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.search_var.get().lower()
        for row in get_all_cards():
            c_id, c_type, g_id, data, locked, created, uid = row
            if query in str(c_id).lower() or query in str(uid).lower() or query in str(c_type).lower():
                lock_str = "Evet" if locked else "Hayır"
                self.tree.insert('', 'end', values=(c_id, c_type, g_id, uid, lock_str))

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        c_id = item['values'][0]
        
        with sqlite3.connect('data/nfc_system.db') as conn:
            row = conn.execute('SELECT data FROM cards WHERE card_id=?', (c_id,)).fetchone()
            if row:
                data = json.loads(row[0])
                self.edit_title_var.set(data.get('title', ''))
                self.edit_json_text.delete('1.0', 'end')
                self.edit_json_text.insert('1.0', json.dumps(data, ensure_ascii=False, indent=2))

    def update_selected_card(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Uyarı", "Lütfen listeden bir kart seçin.")
        c_id = self.tree.item(sel[0])['values'][0]
        try:
            new_data = json.loads(self.edit_json_text.get('1.0', 'end').strip())
            if 'title' in new_data: new_data['title'] = self.edit_title_var.get()
            update_card_data(c_id, new_data)
            self.refresh_routes()
            self.refresh_card_list()
            messagebox.showinfo("Başarılı", "Kart güncellendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Geçersiz JSON: {e}")

    def update_selected_group(self):
        sel = self.tree.selection()
        if not sel: return
        g_id = self.tree.item(sel[0])['values'][2]
        if not g_id: return messagebox.showwarning("Uyarı", "Seçili kartın Grubu yok.")
        if not messagebox.askyesno("Grup Güncelle", f"'{g_id}' grubundaki tüm kartlar güncellenecek. Onaylıyor musunuz?"): return
        try:
            new_data = json.loads(self.edit_json_text.get('1.0', 'end').strip())
            if 'title' in new_data: new_data['title'] = self.edit_title_var.get()
            count = update_group_data(g_id, new_data)
            self.refresh_routes()
            self.refresh_card_list()
            messagebox.showinfo("Başarılı", f"{count} kart güncellendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Geçersiz JSON: {e}")

    def delete_selected_card(self):
        sel = self.tree.selection()
        if not sel: return
        c_id = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Sil", f"{c_id} silinsin mi?"):
            delete_card(c_id)
            self.refresh_routes()
            self.refresh_card_list()

    def git_push_info(self):
        messagebox.showinfo("GitHub Gönderimi", "Sistemi GitHub'a göndermek için CMD'yi açın ve şu komutları çalıştırın:\n\ngit add .\ngit commit -m \"Guncelleme\"\ngit push origin main")

    def on_type_change(self):
        for w in self.dynamic_frame.winfo_children():
            if w is not self.iban_container: w.destroy()
        for w in self.iban_container.winfo_children(): w.destroy()
        self.iban_rows = []
        self.single_fields = {}
        t = self.type_var.get()
        if t == 'Çoklu IBAN Kartı': self.build_iban_form()
        else: self.build_single_form(t)

    def build_iban_form(self):
        ttk.Label(self.iban_container, text='Kart Başlığı:').grid(row=0, column=0, sticky='w')
        self.card_title = tk.StringVar(value='Banka Hesaplarım')
        ttk.Entry(self.iban_container, textvariable=self.card_title, width=25).grid(row=0, column=1, sticky='we', pady=2)
        ttk.Label(self.iban_container, text='Kart Sahibi:').grid(row=0, column=2, sticky='w', padx=5)
        ttk.Entry(self.iban_container, textvariable=self.card_owner_var, width=20).grid(row=0, column=3, sticky='we', pady=2)
        ttk.Button(self.iban_container, text='+ Hesap Ekle', command=self.add_iban_row).grid(row=1, column=0, pady=4)
        self.iban_list_frame = ttk.Frame(self.iban_container)
        self.iban_list_frame.grid(row=2, column=0, columnspan=4, sticky='nsew')
        self.add_iban_row()

    def add_iban_row(self):
        row_frame = ttk.Frame(self.iban_list_frame)
        row_frame.pack(fill='x', pady=2)
        bank_var = tk.StringVar(value='Akbank')
        title_var = tk.StringVar()
        name_var = tk.StringVar()
        iban_var = tk.StringVar()
        ttk.Combobox(row_frame, textvariable=bank_var, values=BANKS, width=12, state='readonly').pack(side='left', padx=2)
        ttk.Entry(row_frame, textvariable=title_var, width=10).pack(side='left', padx=2)
        ttk.Entry(row_frame, textvariable=name_var, width=15).pack(side='left', padx=2)
        ttk.Entry(row_frame, textvariable=iban_var, width=26).pack(side='left', padx=2)
        data = {'frame': row_frame, 'bank': bank_var, 'title': title_var, 'name': name_var, 'iban': iban_var}
        def remove():
            row_frame.destroy()
            self.iban_rows.remove(data)
        ttk.Button(row_frame, text='X', width=3, command=remove).pack(side='left', padx=2)
        self.iban_rows.append(data)

    def build_single_form(self, t):
        if t == 'Dijital Menü': self._field('Başlık:', 'title'); self._field('Menü URL:', 'url', 50)
        elif t == 'Google Yorum': self._field('İşletme Adı:', 'title'); self._field('Yorum URL:', 'url', 50)
        elif t == 'Instagram': self._field('Kullanıcı Adı:', 'username'); self._field('Instagram URL:', 'url', 50)
        elif t == 'WhatsApp': self._field('İsim:', 'title'); self._field('Telefon:', 'phone'); self._field('WhatsApp URL:', 'url', 50)
        elif t == 'Sahibinden Mağaza': self._field('Mağaza Adı:', 'title'); self._field('Mağaza URL:', 'url', 50)
        elif t == 'Özel Bağlantı': self._field('Başlık:', 'title'); self._field('Hedef URL:', 'url', 50)

    def _field(self, label, key, width=40):
        row = ttk.Frame(self.dynamic_frame)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text=label, width=15).pack(side='left')
        var = tk.StringVar()
        ttk.Entry(row, textvariable=var, width=width).pack(side='left', fill='x', expand=True)
        self.single_fields[key] = var

    def collect_data(self):
        t = self.type_var.get()
        if t == 'Çoklu IBAN Kartı':
            accs = []
            for r in self.iban_rows:
                iban = r['iban'].get().strip()
                if not iban: continue
                bank = r['bank'].get()
                accs.append({'bank_name': bank, 'bank_color': BANK_COLORS.get(bank, '#666666'), 'account_title': r['title'].get().strip(), 'recipient': r['name'].get().strip(), 'iban': iban})
            if not accs: return None, 'En az bir IBAN girin.'
            return {'title': self.card_title.get().strip() or 'Banka Hesaplarım', 'owner': self.card_owner_var.get().strip(), 'accounts': accs}, None
        data = {}
        for k, v in self.single_fields.items():
            val = v.get().strip()
            if not val: return None, 'Tüm alanlar doldurulmalıdır.'
            data[k] = val
        return data, None

    def process_card(self):
        if not self.writer.mode:
            return messagebox.showerror("Hata", "Lütfen önce okuyucuya bağlanın.")
        threading.Thread(target=self._process_card_thread, daemon=True).start()

    def _process_card_thread(self):
        data, err = self.collect_data()
        if err: return self.log(f'HATA: {err}')
        
        gate = get_setting('gate_url')
        group_id = self.group_id_var.get().strip()
        is_group = self.mode_var.get() == 'gruplu'
        
        if is_group and not group_id:
            return self.log('HATA: Gruplu mod için Grup ID girin.')

        if not is_group:
            card_id = 'K' + _now().replace(':', '') + str(len(get_all_cards()) + 1).zfill(3)
            idx, total = 1, 1
        else:
            card_id = get_next_card_id(group_id)
            idx, total = self.current_index.get() + 1, self.total_count.get()
            if idx > total: return self.log('Grup doldu. Yeni Grup ID girin.')

        self.log('Kart okutun... (Fiziksel kart bekleniyor)')
        
        # Gerçek donanımdan UID okuma
        uid = None
        start_time = time.time()
        while time.time() - start_time < 30:
            uid = self.writer.wait_for_card()
            if uid: break
            time.sleep(0.5)
            
        if not uid: return self.log('HATA: Kart okunamadı veya zaman aşımı.')

        self.log(f'UID: {uid}')

        if find_by_uid(uid):
            ans = messagebox.askyesno('Kayıtlı Kart', 'Bu UID zaten kayıtlı! Üzerine yazılsın mı?')
            if not ans: return self.log('İptal edildi.')

        target_url = gate + card_id
        self.log(f'Yazılıyor: {target_url}')
        
        # Gerçek Donanıma Yazma
        ok, msg = self.writer.write_ndef_url(target_url, self.chip_var.get())
        self.log(msg)
        if not ok: return

        self.log('Doğrulanıyor...')
        ok, read_back = self.writer.read_ndef_url()
        if not ok or read_back != target_url:
            return self.log('HATA: Doğrulama başarısız! KİLİTLENMEDİ.')
        self.log('Doğrulama başarılı.')

        if self.lock_var.get():
            self.log('Kilit vuruluyor...')
            ok, msg = self.writer.lock_card()
            self.log(msg)
            if not ok: self.log('UYARI: Kilit desteklenmiyor, atlandı.')

        try:
            insert_card(card_id, uid, self.type_var.get(), group_id if is_group else None, data, self.lock_var.get())
            self.refresh_routes()
            winsound.Beep(1200, 150)
            self.log(f'BAŞARILI: {card_id} kaydedildi.')
            
            if not is_group:
                self.root.after(0, self.on_type_change)
                self.log('Form sıfırlandı.')
            else:
                self.current_index.set(idx)
                self.root.after(0, lambda: self.counter_label.config(text=f"{idx} / {total}"))
                self.log(f'Sayaç: {idx}/{total}. Sıradaki kartı okutun.')
        except Exception as e:
            self.log(f'DB HATA: {e}')

    def save_gate(self):
        url = self.gate_entry.get().strip()
        import re
        url = re.sub(r'\?id=.*$', '?id=', url)
        self.gate_entry.delete(0, 'end')
        self.gate_entry.insert(0, url)
        set_setting('gate_url', url)
        set_setting('reader_mode', self.reader_var.get())
        set_setting('chip_type', self.chip_var.get())
        set_setting('lock_card', '1' if self.lock_var.get() else '0')
        self.log('Ayarlar kaydedildi.')

    def connect_reader(self):
        mode = self.reader_var.get()
        if 'PN532' in mode:
            port = simpledialog.askstring('COM Port', 'Port girin (ör. COM3):')
            if port:
                ok, msg = self.writer.connect_pn532(port)
                self.log(msg)
        elif 'ACR122U' in mode:
            ok, msg = self.writer.connect_acr122u()
            self.log(msg)

    def refresh_routes(self):
        try:
            generate_routes('routes.json')
            self.log('routes.json güncellendi.')
        except Exception as e:
            self.log(f'JSON HATA: {e}')

if __name__ == '__main__':
    import time
    root = tk.Tk()
    NFCApp(root)
    root.mainloop()
