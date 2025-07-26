# #!/usr/bin/env python3
# # =============================================================================
# # CS2 Ancient Chinese Secrets – Carmack Edition GUI  (Alpha v0.0004-PATCHED)
# # Fully patched with centralized dropdown utilities + debug logging
# # Timestamp‐TOP: 2025-07-14  
# # =============================================================================

# import logging, sys, os, io, re, threading, time
# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox
# from tkinter.scrolledtext import ScrolledText
# from PIL import Image, ImageTk

# # ——— UTILS FIRST —————————————————————————————————————————————
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
# from dropdown_utils       import parse_player_dropdown
# from round_dropdown_utils import parse_round_dropdown
# from steam_utils          import to_steam2, parse_sid64, normalize_sid
# from pi_fetch             import fetch_scout_data

# # ——— PARSER NEXT ————————————————————————————————————————————
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cs2_parser"))
# from cs2_parser.file_loader   import load_input
# from cs2_parser.event_log     import display_events
# from cs2_parser.stats_summary import display_stats_summary
# from cs2_parser.chat_summary  import display_chat_summary

# PCT_RE      = re.compile(r"(\d{1,3})%")
# ASSET_DIR   = os.path.join(os.path.dirname(__file__), "asset")
# ICON_PATH   = os.path.join(ASSET_DIR, "CS2.png")
# BANNER_GRAY = os.path.join(ASSET_DIR, "CS2-gray.png")
# BANNER_GIF  = os.path.join(ASSET_DIR, "CS2-tb-fill.gif")
# BANNER_COL  = os.path.join(ASSET_DIR, "CS2-col.png")

# logging.basicConfig(level=logging.DEBUG,
#                     format="%(asctime)s %(levelname)s: %(message)s")
# log = logging.getLogger(__name__)

# class Banner(tk.Label):
#     def __init__(self, master, gray, gif, color, w, h, delay=100, **kw):
#         super().__init__(master, **kw)
#         self.gray_tk  = ImageTk.PhotoImage(Image.open(gray).resize((w,h), Image.LANCZOS))
#         self.color_tk = ImageTk.PhotoImage(Image.open(color).resize((w,h), Image.LANCZOS))
#         self.frames   = []
#         gif_img = Image.open(gif)
#         for f in range(getattr(gif_img, "n_frames", 1)):
#             try:
#                 gif_img.seek(f)
#                 frm = gif_img.copy().convert("RGBA").resize((w,h), Image.LANCZOS)
#                 self.frames.append(ImageTk.PhotoImage(frm))
#             except EOFError:
#                 break
#         self.config(image=self.gray_tk)
#         self._delay = delay; self._animating = False; self._idx = 0

#     def start(self):
#         if self.frames and not self._animating:
#             self._animating = True; self._idx = 0; self._animate()
#     def _animate(self):
#         if not self._animating: return
#         self.config(image=self.frames[self._idx])
#         self._idx = (self._idx + 1) % len(self.frames)
#         self.after(self._delay, self._animate)
#     def stop(self):
#         self._animating = False; self.config(image=self.color_tk)

# class CS2ParserApp:
#     def __init__(self, root):
#         root.title("CS2 ACS – Carmack Edition Alpha v0.0004-PATCHED")
#         root.geometry("1100x750"); root.configure(bg="black")
#         if os.path.isfile(ICON_PATH):
#             root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
#         self.root = root; self.json_data = {}; self.rounds = []
#         self._build_ui(); self.set_progress(0)

#     def _build_ui(self):
#         self._style(); self._banner(); self._menu(); self._tabs(); self._bottom()
#         self.nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

#     def _style(self):
#         s=ttk.Style(); s.theme_use("default")
#         s.configure("TNotebook", background="black")
#         s.configure("TNotebook.Tab", background="#111", foreground="white", padding=(10,5))
#         s.map("TNotebook.Tab", background=[("selected","#333")])
#         s.configure("Treeview", background="black", foreground="white", fieldbackground="black", rowheight=20)

#     def _banner(self):
#         f=tk.Frame(self.root,bg="black"); f.pack(fill="x")
#         self.banner=Banner(f,BANNER_GRAY,BANNER_GIF,BANNER_COL,1100,40,delay=50,bg="black")
#         self.banner.pack(fill="x")

#     def _menu(self):
#         mb=tk.Menu(self.root); fm=tk.Menu(mb,tearoff=0)
#         fm.add_command(label="Open Demo/JSON", command=self._on_open)
#         em=tk.Menu(fm,tearoff=0)
#         for fmt in ("pdf","json","nav","log","pulse"):
#             em.add_command(label=f"As {fmt.upper()}", command=lambda f=fmt: self._export(f))
#         fm.add_cascade(label="Export",menu=em); fm.add_separator(); fm.add_command(label="Exit",command=self.root.quit)
#         mb.add_cascade(label="File",menu=fm)
#         hm=tk.Menu(mb,tearoff=0); hm.add_command(label="About", command=self._show_about)
#         mb.add_cascade(label="Help",menu=hm); self.root.config(menu=mb)
#         tools_menu.add_command(label="🧼 Sanitize JSON via Log", command=run_sanitizer_via_gui)

#     #injecting GUI hook for Sanitizer (menu & handlers)
#     # ============================================================================
# # Hook: Add Sanitizer to Menu
# # ============================================================================
# def run_sanitizer_via_gui():
#     """
#     Prompts for both JSON and LOG files, runs sanitizer, displays result.
#     """
#     from tkinter import filedialog, messagebox
#     import data_sanitizer
#     import os

#     json_path = filedialog.askopenfilename(
#         title="Select Parsed Match JSON File",
#         filetypes=[("JSON Files", "*.json")]
#     )
#     if not json_path:
#         return

#     log_path = filedialog.askopenfilename(
#         title="Select Fallback Log File",
#         filetypes=[("Log Files", "*.log")]
#     )
#     if not log_path:
#         return

#     try:
#         # Load .json
#         with open(json_path, "r", encoding="utf-8") as jfile:
#             json_data = json.load(jfile)

#         # Parse .log
#         parsed_log = data_sanitizer.parse_log_file(log_path)

#         # Sanitize
#         patched_json, added_events, added_types = data_sanitizer.sanitize_json_with_log(json_data, parsed_log)

#         # Save output
#         out_prefix = os.path.splitext(os.path.basename(json_path))[0] + "_sanitized"
#         data_sanitizer.write_outputs(patched_json, added_events, added_types, out_prefix)

#         messagebox.showinfo("Sanitizer Complete", f"{len(added_events)} events added.\nOutput saved as {out_prefix}.json")
#     except Exception as e:
#         messagebox.showerror("Sanitizer Failed", f"Error:\n{e}")
# #EOB santizer hook

#     def _tabs(self):
#         self.nb=ttk.Notebook(self.root)
#         self.tab_cons, self.tab_evt, self.tab_stat, self.tab_chat = [tk.Frame(self.nb,bg="black") for _ in range(4)]
#         self.nb.add(self.tab_cons,text="Console"); self.nb.add(self.tab_evt,text="Event Log")
#         self.nb.add(self.tab_stat,text="Advanced Stats"); self.nb.add(self.tab_chat,text="Chat & Summary")
#         self.nb.pack(expand=True,fill="both")
#         # Frames
#         self.stats_frame=tk.Frame(self.tab_stat,bg="black"); self.stats_frame.pack(fill="both",expand=True)
#         self.chat_frame =tk.Frame(self.tab_chat,bg="black"); self.chat_frame.pack(fill="both",expand=True)
#         # Console
#         self.txt_console=ScrolledText(self.tab_cons,bg="black",fg="white",wrap="word",font=("Consolas",10))
#         for lvl,color in [("INFO","cyan"),("DEBUG","gray"),("WARN","yellow"),("ERROR","red")]:
#             self.txt_console.tag_config(lvl,foreground=color)
#         self.txt_console.pack(fill="both",expand=True)
#         # Events
#         self.tree=ttk.Treeview(self.tab_evt,show="tree"); self.tree.pack(fill="both",expand=True)

#     def _bottom(self):
#         f=tk.Frame(self.root,bg="black"); f.pack(fill="x",side="bottom",pady=5)
#         tk.Label(f,text="Player:",fg="white",bg="black").grid(row=0,column=0,padx=5)
#         self.cb_player=ttk.Combobox(f,state="readonly",width=30); self.cb_player.grid(row=0,column=1)
#         self.cb_player.bind("<<ComboboxSelected>>",self._on_selection_change)
#         tk.Label(f,text="Round:",fg="white",bg="black").grid(row=0,column=2,padx=5)
#         self.cb_round =ttk.Combobox(f,state="readonly",width=20); self.cb_round.grid(row=0,column=3)
#         self.cb_round.bind("<<ComboboxSelected>>",self._on_selection_change)
#         for i,label,cmd in [(4,"Replay",self._replay),(5,"Stats",self._gen_stats),(6,"Debug",self._debug)]:
#             tk.Button(f,text=label,command=cmd).grid(row=0,column=i,padx=5)
#         self.pb=ttk.Progressbar(f,length=200,mode="determinate"); self.pb.grid(row=0,column=7,padx=10)

#     def _log(self,msg):
#         level=None
#         for lvl in ("ERROR","WARN","DEBUG","INFO"):
#             if msg.startswith(f"[{lvl}]"): level=lvl; break
#         line=msg.rstrip("\n")+"\n"
#         if level: self.txt_console.insert("end",line,level)
#         else:     self.txt_console.insert("end",line)
#         self.txt_console.see("end")

#     def set_progress(self,val): self.pb['value']=val

#     def _on_open(self):
#         path=filedialog.askopenfilename(title="Select Demo/JSON",filetypes=[("Demo .dem","*.dem"),("JSON","*.json")])
#         if not path: return
#         self.banner.start(); self.txt_console.delete("1.0","end"); self.nb.select(self.tab_cons)
#         threading.Thread(target=self._process,args=(path,),daemon=True).start()

#     def _process(self,path):
#         buf=io.StringIO(); hdl=logging.StreamHandler(buf); hdl.setLevel(logging.DEBUG)
#         lg=logging.getLogger(); lg.addHandler(hdl)
#         start=time.time()
#         try:
#             data=load_input(path,lambda line:self.root.after(0,lambda:self._log(line)))
#         except Exception as e:
#             # capture the error string into the callback
#             err = f"[ERROR] Parser error: {e}"
#             self.root.after(0, lambda err=err: self._log(err))
#             lg.removeHandler(hdl)
#             return
#             lg.removeHandler(hdl); return
#         lg.removeHandler(hdl); self.json_data=data
#         duration=time.time()-start; output=buf.getvalue().splitlines()
#         self.root.after(0,lambda:self._on_loaded(output,duration))

#     def _on_loaded(self,output,duration):
#         self.banner.stop(); self.set_progress(100)
#         for ln in output: self._log(ln)
#         evs=self.json_data.get("events",[]); self._log(f"[INFO] Parsed {len(evs)} events in {duration:.2f}s")
#         self._populate_players(); self._populate_rounds()
#         self._log(f"[DEBUG] display_events → tree:{type(self.tree)}, events:{len(evs)}")
#         try: display_events(self.tree,self.json_data)
#         except Exception as ex:
#             self._log(f"[ERROR] display_events failed: {ex}")
#             import traceback; 
#             for tl in traceback.format_exc().splitlines(): self._log(f"[ERROR] {tl}")

#     def _populate_players(self):
#         parsed=parse_player_dropdown(self.json_data.get("playerDropdown",[]))
#         self.player_map={f"{p['name']} ({p['steamid2']})":p['steamid64'] for p in parsed}
#         names=list(self.player_map.keys()); self.cb_player.config(values=names)
#         if names: self.cb_player.current(0)

#     def _populate_rounds(self):
#         indices,labels=parse_round_dropdown(self.json_data.get("events",[]))
#         self.rounds=indices; self.cb_round.config(values=labels)
#         if labels: self.cb_round.current(0)

#     def _on_tab_change(self,evt):
#         sel=evt.widget.select()
#         if sel==str(self.tab_cons): self._refresh_console()
#         if sel==str(self.tab_evt):  self._refresh_events()
#         if sel==str(self.tab_stat): self._refresh_stats()
#         if sel==str(self.tab_chat): self._refresh_chat()

#     def _on_selection_change(self,*_):
#         self._refresh_stats(); self._refresh_chat()

#     def _refresh_console(self): self.txt_console.see("end")
#     def _refresh_events(self): self.tree.delete(*self.tree.get_children()); display_events(self.tree,self.json_data)
#     def _refresh_stats(self):
#         idx=self.cb_round.current()
#         rd=self.rounds[idx] if 0<=idx<len(self.rounds) else None
#         display_stats_summary(self.stats_frame,self.json_data,rd)
#     def _refresh_chat(self): display_chat_summary(self.chat_frame,self.json_data)
#     def _replay(self): self._log(f"[INFO] 🔄 Replay {self.cb_player.get()} {self.cb_round.get()}")
#     def _gen_stats(self): self._log(f"[INFO] 📊 Stats for {self.cb_player.get()} {self.cb_round.get()}")
#     def _debug(self): self._log(f"[DEBUG] {self.json_data}")
#     def _export(self,fmt): messagebox.showinfo("Export",f"Exporting as {fmt.upper()}")
#     def _show_about(self): messagebox.showinfo("About","CS2 ACS GUI – Demonstration Build.")

# if __name__=="__main__":
#     root=tk.Tk(); app=CS2ParserApp(root); root.mainloop()
# # EOF <AR <3 centralized utils & debug overhaul | TLOC ~360 | 2025-07-14T00:00-04:00
# # EOF pzr1H 215ln - testing

##old main ^^ 