
#######外部ライブラリ#######
import wx
import wx.grid as gridlib
import wx.lib.scrolledpanel as scrl
import pandas as pd
import numpy as np
import cv2
##########################
import sys,os
import random
import csv


#メイン画面のフレーム
class MainFrame(wx.Frame):

    #起動時の初期化
    def __init__(self):
        global img_adr #画像データのパス
        global memory #座標データを格納するリスト
        global img_size #画像のサイズ(幅x高さxチャンネル数)
        global main_panel #アプリケーションウィンドウのパネル
        global img_panel #選択した画像を表示するパネル
        global select_area_number #任意の亀裂の番号
        global judge_and_make #ラジオボックスで亀裂のラベリングをするためのパネル
        global save_name #CSVデータを保存する時のファイル名
        global save_path #CSVデータを保存するパス
        global new_pos_set #新しく指定した亀裂の座標データを格納するリスト
        global os_type #アプリケーションを使用するOSの種類(WindowsとLinuxに対応)
        global edit_files #アプリケーション起動中に編集したCSVデータのパスを格納するリスト
        global already_exists #アプリケーション起動中にCSVデータを編集した回数

        wx.Frame.__init__(self,None,wx.ID_ANY,u"Crack Detect Gui",size = (675,830))
        self.SetBackgroundColour("#888888")
        self.CreateStatusBar()

        self.SetMenuBar(Setmenu())
        img_adr = ""
        save_name = ""
        save_path = ""
        memory = []
        img_size = 0
        new_pos_set = []
        edit_files = []
        already_exists = {}

        os_type = os.name
        self.file_filter = ("csv file(*.csv) | *.csv")

        self.Bind(wx.EVT_MENU,self.menu_function)

        main_panel =wx.Panel(self,wx.ID_ANY)
        main_panel.SetBackgroundColour("#888888")

        self.text_panel = wx.Panel(main_panel,wx.ID_ANY,pos = (0,0),size = (200,30),style = wx.BORDER_RAISED) #テキストを入れる領域の生成(ウィンドウの左上を(0,0)として200x30の領域を生成)
        self.label_panel = wx.Panel(main_panel,wx.ID_ANY,pos = (0,30),size = (200,720),style = wx.BORDER_RAISED) #テキストを入れる領域の生成(座標(0,30)を左上としたサイズ200x720ピクセルの領域を生成)

        wx.StaticText(self.text_panel,wx.ID_ANY,u"画像一覧",pos = (60,8)) #生成したself.text_panelに文字を設定
        self.image_listbox = wx.ListBox(self.label_panel,wx.ID_ANY,size = (200,720),style = wx.LB_SORT) #画像一覧を表示するリストを表示するための領域
        self.image_listbox.Bind(wx.EVT_LISTBOX_DCLICK,self.showimage)

        img_panel = Image_viewer(main_panel) #画像を表示するための領域生成
        img_panel.SetBackgroundColour("#ffffff")

        judge_and_make = Judge_and_Make(main_panel,memory) #画像のラベリングの際に現れるラジオボックスの領域生成
        judge_and_make.SetBackgroundColour("#888888")

        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(self.image_listbox)
        layout.Add(img_panel,wx.SHAPED | wx.LEFT)

        main_panel.SetSizer(layout)


    #メニューバーの各メニューの機能(”ファイル”にitem_idが1~6の機能、”クラック”に7〜8の機能を表示、item_idが3の機能だけ未実装)
    def menu_function(self,event):

        global img_adr
        global main_panel
        global memory
        global img_size
        global os_type
        global edit_files
        global already_exists

        item_id = event.GetId()

        #画像が保存されているフォルダを選択しその一覧を表示する機能
        if item_id == 1:
            self.SetStatusText(u"画像フォルダを開く")
            self.imgfolder()

        #print文で選択したファイル表示するだけの機能(file_createメソッド内で処理を記述)
        elif item_id == 2:
            self.SetStatusText(u"データセットを開く")
            self.file_create()

        #データセットの中身(CSVファイル)を編集する機能
        elif item_id == 4:
            edit_daialog = wx.FileDialog(None,u"ファイルを選択",style = wx.FD_OPEN)
            ok_or_cancel = edit_daialog.ShowModal()
            self.file_path = edit_daialog.GetPath()
            if os_type == "posix":
                file_n = self.file_path.rsplit("/",1)
            elif os_type == "nt":
                file_n = self.file_path.rsplit("\\",1)
            data_existence = self.file_path.rsplit(".",1)

            if ok_or_cancel == wx.ID_OK or data_existence[1] == "csv":
                if os_type == "posix" and data_existence[1] == "csv":
                    os.system("soffice %s"%self.file_path)
                    os.system("exit")
                elif os_type == "nt" and data_existence[1] == "csv":
                   os.system("%s"%self.file_path)
                elif data_existence[1] == "csv":
                    self.df = pd.read_csv(self.file_path,delimiter = ',')
                    already_flag = 0
                    if edit_files == []:
                        edit_files.append(file_n[1])
                        edit_csv_frame = wx.Frame(None,wx.ID_ANY,"CSV file Editor：%s"%file_n[1],size = wx.Size(650,600)) #csvファイルを編集するウィンドウのサイズ指定
                        edit_csv_panel = wx.Panel(edit_csv_frame,wx.ID_ANY)
                    elif edit_files != []:
                        if file_n[1] in edit_files:
                            if file_n[1] not in already_exists:
                                already_exists[file_n[1]] = 0
                            else:
                                already_exists[file_n[1]] += 1
                            edit_csv_frame = wx.Frame(None,wx.ID_ANY,"CSV file Editor：%s(%s)"%(file_n[1],already_exists[file_n[1]]+1),size = wx.Size(650,600))
                            edit_csv_panel = wx.Panel(edit_csv_frame,wx.ID_ANY)
                        else:
                            edit_files.append(file_n[1])
                            edit_csv_frame = wx.Frame(None,wx.ID_ANY,"CSV file Editor：%s"%file_n[1],size = wx.Size(650,600))
                            edit_csv_panel = wx.Panel(edit_csv_frame,wx.ID_ANY)
                    print(already_exists)
                    self.grid = gridlib.Grid(edit_csv_panel,size = wx.Size(650,600))
                    self.grid.CreateGrid(len(self.df),7)
                    self.grid.SetColLabelValue(0,"File name")
                    self.grid.SetColLabelValue(1,"File size")
                    self.grid.SetColLabelValue(2,"File Attributes")
                    self.grid.SetColLabelValue(3,"Region count")
                    self.grid.SetColLabelValue(4,"Region id")
                    self.grid.SetColLabelValue(5,"Region shape attributes")
                    self.grid.SetColLabelValue(6,"Region attirbutes")

                    for i in range(0,len(self.df),1):
                        nan_signal = str(self.df.ix[i][0])
                        if nan_signal != "nan":
                            for j in range(0,7,1):
                                self.grid.SetCellValue(i,j,str(self.df.ix[i][j]))

                    sizer = wx.BoxSizer(wx.HORIZONTAL)
                    sizer.Add(self.grid,1,wx.EXPAND)

                    save_type = wx.Menu()
                    save_type.Append(1,"名前を変えて保存")
                    save_type.Append(2,"上書き保存")
                    save_type.Append(3,"全体を終了")
                    editor_menu_bar = wx.MenuBar()

                    editor_menu_bar.Append(save_type,"変更を保存")
                    edit_csv_frame.Bind(wx.EVT_MENU,self.save_edit_file)
                    edit_csv_frame.SetMenuBar(editor_menu_bar)

                    edit_csv_panel.SetSizer(sizer)
                    edit_csv_frame.Show()
            else:
                mistake_file = wx.MessageDialog(self,"ファイル形式が違います。\nCSV形式のファイルを選択して下さい。","Selected file is mistake.",style = wx.OK)
                mistake_file.ShowModal()

        #アプリケーションを終了
        elif item_id == 5:
            self.SetStatusText(u"終了")
            sys.exit()

        #デバック用の機能
        elif item_id == 6:
            print(memory)
            print(img_adr)
            print(int(img_size))

        #デバック用の機能
        elif item_id == 7:
            self.draw_rectangle(memory)

        #亀裂の領域を手動で選択する機能
        elif item_id == 8:
            self.SetStatusText(u"新規クラック領域の指定")

            if img_adr == "":
                dialog_8 = wx.MessageDialog(self,'画像を参照できません。',"Image couldn't capture.",style = wx.OK | wx.ICON_QUESTION)
                dialog_8.ShowModal()

            elif img_adr != "":

                if memory == []:
                    before_detect_dialog = wx.MessageDialog(self,u"先に検出を行ってください","You haven't detected cracks yet.",wx.OK)
                    before_detect_dialog.ShowModal()

                elif memory != []:
                    base_img = wx.Bitmap(img_adr)
                    for_get_size_img_re = cv2.imread(img_adr)
                    base_height,base_width = for_get_size_img_re.shape[:2]

                    # 別のウィンドウで表示する際に画像サイズを調整
                    if base_width > 700 or base_height > 700:
                        if base_width > 700:

                            resize_w = base_width / (base_width / 700)
                            resize_h = base_height / (base_width / 700)
                            base_img = self.scale_image(img_adr,resize_w,resize_h)
                            resize_ratio = 700 / base_width

                        elif base_height > 700:

                            resize_w = base_width / (base_height / 700)
                            resize_h = base_height / (base_height / 700)
                            base_img = self.scale_image(img_adr,resize_w,resize_h)
                            resize_ratio = 700 / base_height

                    else:
                        if base_width > base_height:

                            resize_w = 700
                            resize_h = 700 * (base_height / base_width)
                            resize_ratio = 700 / base_width
                            print(resize_ratio)
                            base_img = self.scale_image(img_adr,resize_w,resize_h)

                        elif base_width < base_height:
                            resize_w = 700 * (base_width / base_height)
                            resize_h = 700
                            resize_ratio = 700 / base_height
                            print(resize_ratio)
                            base_img = self.scale_image(img_adr,resize_w,resize_h)
                    adding_crack_frame = Add_new_cracks(self,resize_w,resize_h,resize_ratio,base_img)
                    adding_crack_frame.Show()

        #画像を大きいサイズで確認する機能
        elif item_id == 9:

            viewer_frame = Original_image(self)
            viewer_frame.Show()

            if img_adr == "":
                dialog_9 = wx.MessageDialog(viewer_frame,'画像を参照できません。',"Image couldn't capture.",style = wx.OK | wx.ICON_QUESTION)
                dialog_9.ShowModal()
                viewer_frame.Destroy()

            elif img_adr != "":
                sc_window = wx.ScrolledWindow(viewer_frame,wx.ID_ANY,size = (800,800)) #画像ビューアを表示する時のウィンドウサイズの指定
                original_view = wx.Image(img_adr)
                scroll_width = original_view.GetWidth()
                scroll_height = original_view.GetHeight()
                conv_bitmap = original_view.ConvertToBitmap()
                wx.StaticBitmap(sc_window,wx.ID_ANY,conv_bitmap,(0,0))
                sc_window.SetScrollbars(10,10,scroll_width/10,scroll_height/10)
            viewer_frame.Show()


    #編集したCSVファイルを保存
    def save_edit_file(self,event):

        global os_type

        save_id = event.GetId()

        #新規にファイルを作成した上で保存
        if save_id == 1:
            edit_confirmation = wx.MessageDialog(self,'名前を付けて保存しますか？','Save confirmation',style = wx.YES_NO)
            save_or_not = edit_confirmation.ShowModal()
            edit_confirmation.Destroy()

            if save_or_not == wx.ID_YES:
                alter_name = ""
                file_redundancy_flag = 0

                save_daialog = wx.FileDialog(None,u"ファイルを選択",wildcard = "*.csv",style = wx.FD_SAVE)
                save_signal = save_daialog.ShowModal()

                alter_name = save_daialog.GetFilename()
                get_directory = save_daialog.GetDirectory()

                if alter_name != "":
                    alter_path = save_daialog.GetPath()
                    get_any_file = os.listdir(get_directory)

                    if os_type == "posix":
                        alter_file_n = alter_path.rsplit("/",1)
                    elif os_type == "nt":
                        alter_file_n = alter_path.rsplit("\\",1)

                    for redundancy_n in get_any_file:
                        if alter_file_n[1] == redundancy_n:
                            file_redundancy = wx.MessageDialog(self,"同じ名前ファイルが存在しています。\n違うファイル名にして下さい。","File name is redundancy.",style = wx.OK)
                            file_redundancy.ShowModal()
                            file_redundancy_flag = 1
                            break

                    if file_redundancy_flag != 1:
                        f_register = []
                        w_register = []
                        col_index = ["#filename","file_size","file_attributes","region_count","region_id","region_shape_attributes","region_attributes"]

                        for k in range(0,len(self.df),1):
                            for m in range(0,7,1):
                                w_register.append(self.grid.GetCellValue(k,m))
                            f_register.append(w_register)
                            w_register = []

                        with open(alter_path,'a', newline = '') as fw:
                            writer = csv.writer(fw)
                            writer.writerow(col_index)
                            for c in range(0,len(self.df),1):
                                writer.writerow(f_register[c])

                        print("file name:%s"%alter_path)

        #指定のファイルに上書きして保存
        elif save_id == 2:
            edit_confirmation = wx.MessageDialog(self,'上書き保存します\nよろしいですか？','Save confirmation',style = wx.YES_NO)
            save_or_not = edit_confirmation.ShowModal()
            edit_confirmation.Destroy()

            if save_or_not == wx.ID_YES:

                os.system("del %s"%self.file_path)

                f_register = []
                w_register = []
                col_index = ["#filename","file_size","file_attributes","region_count","region_id","region_shape_attributes","region_attributes"]

                for k in range(0,len(self.df),1):
                    for m in range(0,7,1):
                        w_register.append(self.grid.GetCellValue(k,m))
                    f_register.append(w_register)
                    w_register = []

                with open(self.file_path,'a') as fw:
                    writer = csv.writer(fw)
                    writer.writerow(col_index)
                    for c in range(0,len(self.df),1):
                        writer.writerow(f_register[c])

        #プログラムごと終了
        elif save_id == 3:
            sys.exit()


    #検出した亀裂全てを一度に表示
    def draw_rectangle(self,pos):

        global img_adr
        global img_width #リサイズ後の画像の幅
        global img_height #リサイズ後の画像の高さ
        global img_panel
        global main_panel
        global viewer_panel #img_panelに画像を貼り付けるためのパネル

        i = 0
        count = 0

        base_image = cv2.imread(img_adr)

        number = len(pos)

        for i in range(number):
            count += 1
            drew = cv2.rectangle(base_image,(pos[i][0],pos[i][1]),(pos[i][0]+pos[i][2],pos[i][1]+pos[i][3]),(0,0,255),2)

        print("finished")
        drew = cv2.resize(drew,(int(img_width),int(img_height)))

        cv2.imwrite("drew1.jpg",drew)
        detect_image = wx.Image("drew1.jpg")
        drew_bmp = detect_image.ConvertToBitmap()

        bbit = wx.Bitmap(460,460)
        dc = wx.ClientDC(viewer_panel)
        dc.Clear()
        dc.DrawBitmap(drew_bmp,0,0,True)
        os.remove("drew1.jpg")


    #画像を保存したフォルダを指定してその一覧をリストとして表示
    def imgfolder(self):

        global main_panel

        self.folder = wx.DirDialog(None,u"画像フォルダの選択")
        folder_signal = self.folder.ShowModal()

        if folder_signal == wx.ID_OK:
            self.folder_list = os.listdir(self.folder.GetPath())

            self.folder_img = []
            for f in self.folder_list:
                name,ext = os.path.splitext(f)
                if ext == ".jpg" or ext == ".png" or ext == ".JPG" or ext == ".PNG" or ext == ".BMP" or ext == ".jpeg":
                    self.folder_img.append(f)

            image_num = len(self.folder_img)
            self.text_panel.Destroy()
            self.text_panel = wx.Panel(main_panel,wx.ID_ANY,pos = (0,0),size = (200,30),style = wx.BORDER_RAISED)
            wx.StaticText(self.text_panel,wx.ID_ANY,u"画像一覧（%d枚）"%image_num,pos = (45,8))
            old_data = self.image_listbox.GetCount()
            if old_data is not None:
                self.image_listbox.Clear()
            for n in range(image_num):
                self.image_listbox.Append(self.folder_img[n])

        if folder_signal == wx.ID_CANCEL:
            pass


    #選択したフォルダの画像リストから一つの画像ファイル名をダブルクリックするとその画像を表示
    def showimage(self,event):

        global img_adr
        global img_width
        global img_height
        global img_size
        global main_panel
        global img_panel
        global viewer_panel
        global os_type

        img_adr = ""
        dir_adr = self.folder.GetPath()
        name_adr = self.image_listbox.GetStringSelection()

        #Windowsの場合パスの区切りを"\\"、Linuxの場合"/"として扱う
        if os_type == "nt":
            img_adr = dir_adr + "\\" + name_adr
        elif os_type == "posix":
            img_adr = dir_adr + "/" + name_adr
        img_size = 0
        image = wx.Image(img_adr)

        for_get_size_img = cv2.imread(img_adr)
        height,width = for_get_size_img.shape[:2]

        if width > 460:
            print("width over")
            if height > 460:
                print("Both over")
                if width > height:
                    print("width > height")
                    print("width:%d , height:%d"%(width,height))
                    new_w = width / (width / 460)
                    new_h = height / (width / 460)
                    image = self.scale_image(img_adr,new_w,new_h)
                    img_width = new_w
                    img_height = new_h

                elif width < height:
                    print("height > width")
                    print("width:%d , height:%d"%(width,height))
                    new_w = width / (height / 460)
                    new_h = height / (height / 460)
                    image = self.scale_image(img_adr,new_w,new_h)
                    img_width = new_w
                    img_height = new_h

            elif height <= 460:
                print("width over height (less or equal)")
                new_w = width / (width / 460)
                new_h = height / (width / 460)
                image = self.scale_image(img_adr,new_w,new_h)
                img_width = new_w
                img_height = new_h

        elif width == 460:
            print("width equal")
            if width < height:
                print("height > width")
                new_w = width / (height / 460)
                new_h = height / (height / 460)
                image = self.scale_image(img_adr,new_w,new_h)
                img_width = new_w
                img_height = new_h

            elif width > height:
                print("width > height")
                new_w = width / (width / 460)
                new_h = height / (width / 460)
                image = self.scale_image(img_adr,new_w,new_h)
                img_width = new_w
                img_height = new_h

            elif height == 460:
                print("Both equal")
                img_width = width
                img_height = height

        elif width < 460:
            print("width less")
            if height < 460:
                print("Both less")
                if width < height:
                    print("height > width")
                    new_w = width / (height / 460)
                    new_h = height / (height / 460)
                    image = self.scale_image(img_adr,new_w,new_h)
                    img_width = new_w
                    img_height = new_h

                elif width > height:
                    print("width > height")
                    new_w = width / (width / 460)
                    new_h = height / (width / 460)
                    image = self.scale_image(img_adr,new_w,new_h)
                    img_width = new_w
                    img_height = new_h

            elif height >= 460:
                print("width less height (over or equal)")
                new_w = width / (height / 460)
                new_h = height / (height / 460)
                image = self.scale_image(img_adr,new_w,new_h)
                img_width = new_w
                img_height = new_h

        img_size = img_height * img_width
        img_panel.Destroy()
        img_panel = Image_viewer(main_panel)
        img_panel.SetBackgroundColour("#ffffff")

        bbit = wx.Bitmap(460,460)
        dc = wx.ClientDC(viewer_panel)
        dc.Clear()
        dc.DrawBitmap(image,0,0,True)

        return [img_adr,img_size]


    #選択したファイルのパスを標準出力で表示、詳細なところまで実装していませんでいた。
    def file_create(self):
        file = wx.FileDialog(None,u"ファイルを選択してください")
        file.ShowModal()
        self.file = file.GetPath()
        print(self.file)


    #表示用に画像をリサイズ
    def scale_image(self,img,width,height):
        imag = cv2.imread(img,cv2.COLOR_BGR2RGB)
        buf = cv2.resize(imag,None,fx = width/imag.shape[1],fy = height/imag.shape[0])
        cv2.imwrite("temp.jpg",buf)
        temp_read = wx.Image("temp.jpg")
        bmp = temp_read.ConvertToBitmap()

        return bmp


#メニューバーの構築
class Setmenu(wx.MenuBar):

    def __init__(self):

        wx.MenuBar.__init__(self)

        menu_file = wx.Menu()
        menu_file.Append(1,u"画像フォルダを開く")
        menu_file.Append(2,u"データセットを開く")
        menu_file.Append(3,u"データセット上書き")
        menu_file.Append(4,u"データセットの編集")
        menu_file.Append(5,u"終了")
        menu_file.Append(6,u"ステータス表示")

        menu_crack = wx.Menu()
        menu_crack.Append(7,u"クラック候補を検出")
        menu_crack.Append(8,u"新規クラック領域を指定")
        menu_crack.Append(9,u"画像ビューア")

        self.Append(menu_file,u"ファイル")
        self.Append(menu_crack,u"クラック")


#クラックが検出されないもしくは検出箇所にクラックが含まれなかった場合、手動で領域を選択するためのフレーム
class Add_new_cracks(wx.Frame):

    #新規クラックの入力画面の初期化
    def __init__(self,parent,width,height,ratio,bmp_img):
        wx.Frame.__init__(self,None,wx.ID_ANY,u"新規クラック領域生成",size = (width,height+155))

        self.area_register = []
        self.area_value = []
        self.new_pos = []
        self.new_pos_set = []
        self.redraw_img = bmp_img
        self.restration_r = ratio

        self.add_buttons_panel = wx.Panel(self,wx.ID_ANY,size = (width,30))
        self.new_area_image_panel = wx.Panel(self,wx.ID_ANY,size = (width,height))
        self.new_area_list_panel = wx.Panel(self,wx.ID_ANY,size = (width,100))

        cancel_button = wx.Button(self.add_buttons_panel,wx.ID_ANY,u"選択をキャンセル")
        area_add_button = wx.Button(self.add_buttons_panel,wx.ID_ANY,u"新規領域を追加")
        clear_button = wx.Button(self.add_buttons_panel,wx.ID_ANY,u"やり直す")

        cancel_button.Bind(wx.EVT_BUTTON,self.select_cancel)
        area_add_button.Bind(wx.EVT_BUTTON,self.add_area)
        clear_button.Bind(wx.EVT_BUTTON,self.new_area_list_clear)
        button_arange = wx.BoxSizer(wx.HORIZONTAL)
        button_arange.Add(cancel_button)
        button_arange.Add(area_add_button)
        button_arange.Add(clear_button)

        self.add_buttons_panel.SetSizer(button_arange)

        show_size_img = wx.StaticBitmap(self.new_area_image_panel,wx.ID_ANY,self.redraw_img,(0,0))
        show_size_img.Bind(wx.EVT_LEFT_DCLICK,self.select_new_area)

        self.new_area_listbox = wx.ListBox(self.new_area_list_panel,size = (width,100))
        self.new_area_listbox.Bind(wx.EVT_LISTBOX,self.re_display)
        self.new_area_listbox.Bind(wx.EVT_LISTBOX_DCLICK,self.del_area)

        layout_new = wx.BoxSizer(wx.VERTICAL)
        layout_new.Add(self.new_area_image_panel)
        layout_new.Add(self.add_buttons_panel)
        layout_new.Add(self.new_area_list_panel)

        self.SetSizer(layout_new)


    #新しいクラックの領域を選択し追加する機能
    def select_new_area(self,event):
        pos = event.GetPosition()
        pdc = wx.WindowDC(self)
        p_color = wx.Pen(wx.Colour(0,0,255))
        pdc.SetPen(p_color)
        pdc.DrawCircle(pos[0],pos[1],3)
        self.area_register.append(pos)

        self.dc = wx.WindowDC(self)
        if len(self.area_register) == 2:

            true_x = 0
            true_y = 0
            true_w = 0
            true_h = 0

            self.dc.DrawBitmap(self.redraw_img,0,0,useMask = True)
            pen = wx.Pen(wx.Colour(255,133,33))
            self.dc.SetPen(pen)

            x1 = self.area_register[0][0]
            y1 = self.area_register[0][1]
            x2 = self.area_register[1][0]
            y2 = self.area_register[1][1]
            self.dc.DrawLine(x1,y1,x2,y1)
            self.dc.DrawLine(x2,y1,x2,y2)
            self.dc.DrawLine(x1,y1,x1,y2)
            self.dc.DrawLine(x1,y2,x2,y2)

            if x1 < x2:
                true_x = x1
                true_w = x2 - x1
            elif x1 > x2:
                true_x = x2
                true_w = x1 - x2

            if y1 < y2:
                true_y = y1
                true_h = y2 - y1
            elif y1 > y2:
                true_y = y2
                true_h = y1 - y2

            self.area_value = [int(true_x),int(true_y),int(true_w),int(true_h)]
            self.new_area_listbox.Append("x:%d,y:%d,w:%d,h:%d"%(true_x,true_y,true_w,true_h))
            self.area_value = []
            self.area_register = []


    #選択した領域の可視化
    def re_display(self,event):
        get_column = event.GetEventObject()
        get_name_and_val = get_column.GetStringSelection().split(",")
        self.re_pos = []

        for l in get_name_and_val:
            get_val = l.split(":")
            if get_val[0] == "x":
                self.re_pos.append(get_val[1])
            elif get_val[0] == "y":
                self.re_pos.append(get_val[1])
            elif get_val[0] == "w":
                self.re_pos.append(get_val[1])
            elif get_val[0] == "h":
                self.re_pos.append(get_val[1])

        x1 = int(self.re_pos[0])
        y1 = int(self.re_pos[1])
        x2 = x1 + int(self.re_pos[2])
        y2 = y1 + int(self.re_pos[3])

        self.dc.DrawBitmap(self.redraw_img,0,0,useMask = True)
        pen = wx.Pen(wx.Colour(133,255,255))
        self.dc.SetPen(pen)

        self.dc.DrawLine(x1,y1,x2,y1)
        self.dc.DrawLine(x2,y1,x2,y2)
        self.dc.DrawLine(x1,y1,x1,y2)
        self.dc.DrawLine(x1,y2,x2,y2)


    #選択した領域の座標データを削除するための機能
    def del_area(self,event):
        col_num = event.GetSelection()
        alert_dialog = wx.MessageDialog(self,u"本当に削除しますか？","Deliting selected position.",style = wx.YES_NO | wx.ICON_INFORMATION)
        del_res = alert_dialog.ShowModal()
        if del_res == wx.ID_YES:
            self.new_area_listbox.Delete(col_num)


    #選択の途中で選択ミスに気づいた場合、その選択を取り消す機能
    def select_cancel(self,event):
        try:
            self.dc.DrawBitmap(self.redraw_img,0,0,useMask = True)
            self.area_value = []
            self.area_register = []
        except:
            error_dialog = wx.MessageDialog(self,u"座標を指定していません","Point was not selected.",style = wx.OK | wx.ICON_ERROR)
            error_dialog.ShowModal()


    #選択した1つ以上の新規領域の座標を、画像処理で検出した座標のデータに追加
    def add_area(self,event):
        global new_pos_set
        global memory
        global judge_and_make
        global main_panel
        global img_panel
        global select_ctrl_panel #任意の亀裂を選択するためのスピンコントロール
        global select_area_number

        judge_and_make.Destroy()

        selected_areas = self.new_area_listbox.GetItems()
        f_split_2 = []
        for f in selected_areas:
            f_split = f.split(",")
            for g in f_split:
                f_split_2 = g.split(":")
                if f_split_2[0] == "x":
                    self.new_pos.append(int(int(f_split_2[1]) / self.restration_r))
                elif f_split_2[0] == "y":
                    self.new_pos.append(int(int(f_split_2[1]) / self.restration_r))
                elif f_split_2[0] == "w":
                    self.new_pos.append(int(int(f_split_2[1]) / self.restration_r))
                elif f_split_2[0] == "h":
                    self.new_pos.append(int(int(f_split_2[1]) / self.restration_r))

        new_pos_set = [self.new_pos[y:y+4] for y in range(0,len(self.new_pos),4)]

        if new_pos_set != []:
            memory = np.concatenate([memory,new_pos_set])

        judge_and_make = Judge_and_Make(main_panel,memory)
        judge_and_make.SetBackgroundColour("#dddddd")

        select_ctrl_panel.Destroy()
        select_ctrl_panel = wx.Panel(img_panel,wx.ID_ANY,pos = (230,460),size = (230,30))
        select_ctrl_panel.SetBackgroundColour("#aaaaaa")

        self.select_ctrl = wx.SpinCtrl(select_ctrl_panel,wx.ID_ANY,value = "1",min = 1,max = len(memory),size = (230,30))
        self.select_ctrl.Bind(wx.EVT_SPINCTRL,img_panel.select_area_number)

        new_added_dialog = wx.MessageDialog(self,u"領域数を変更しました。",u"New pisition datas were added.",style = wx.OK)
        new_added_dialog.ShowModal()
        self.Close()

    #選択した新規領域の領域データを全て消し、最初からやり直す機能
    def new_area_list_clear(self,event):

        clear_dialog = wx.MessageDialog(self,u"本当にやり直しますか？","All Clear.",style = wx.YES_NO | wx.ICON_INFORMATION)
        clear_res = clear_dialog.ShowModal()
        if clear_res == wx.ID_YES:
            self.new_area_listbox.Clear()


#選択した画像を拡大したサイズで表示(別フレームで画像を描画しているだけです。)
class Original_image(wx.Frame):

    def __init__(self,parent):
        wx.Frame.__init__(self,parent,wx.ID_ANY,u"画像ビューア",size = (800,820))
        img_area = wx.Panel(self,wx.ID_ANY)


#メイン画面の中央から右側にかけて表示されている部分(画像、”Detect Crack”のボタン、テキストボックスがある部分)
class Image_viewer(wx.Panel):

    def __init__(self,parent):

        global memory
        global img_adr
        global select_ctrl_panel
        global viewer_panel

        wx.Panel.__init__(self,parent,wx.ID_ANY,pos = (200,0),size = wx.Size(490,490))

        self.button_panel = wx.Panel(self,wx.ID_ANY,size = wx.Size(230,30),pos = (0,460))
        viewer_panel = wx.Panel(self,wx.ID_ANY,pos = (0,0),size = (460,460),style = wx.BORDER_RAISED)
        select_ctrl_panel = wx.Panel(self,wx.ID_ANY,pos = (230,460),size = (230,30))

        self.button_panel.SetBackgroundColour("#ffffff")
        viewer_panel.SetBackgroundColour("#ffffff")
        select_ctrl_panel.SetBackgroundColour("#ffffff")

        self.detect_but = wx.Button(self.button_panel,wx.ID_ANY,u"Detect Cracks.",size = (230,30))
        self.detect_but.SetBackgroundColour("#aaffcc")
        self.select_ctrl = wx.SpinCtrl(select_ctrl_panel,wx.ID_ANY,value = "1",min = 1,size = (230,30))

        self.detect_but.Bind(wx.EVT_BUTTON,self.get_position)
        self.select_ctrl.Bind(wx.EVT_SPINCTRL,self.select_area_number)

        but_lay = wx.BoxSizer(wx.HORIZONTAL)
        ctrl_lay = wx.BoxSizer(wx.HORIZONTAL)

        but_lay.Add(self.detect_but)
        ctrl_lay.Add(self.select_ctrl)

        self.button_panel.SetSizer(but_lay)
        select_ctrl_panel.SetSizer(ctrl_lay)


    #画像からクラックを検出し、検出した数だけラベル付与用のラジオボックスを生成
    def get_position(self,event):

        global memory
        global img_adr
        global img_width
        global img_height
        global main_panel
        global judge_and_make
        global new_pos_set
        global select_ctrl_panel
        global os_type
        global attention_name #選択中の画像のファイル名

        if img_adr != "":
            if os_type == "nt":
                attention_name = img_adr.rsplit("\\",1)
            elif os_type == "posix":
                attention_name = img_adr.rsplit("/",1)

            memory = 0
            print("serching...")
            pos = []

            img_filt = cv2.imread(img_adr)
            print(img_adr)

            min_table = 10
            max_table = 150
            diff_table = max_table - min_table
            lut = np.arange(256,dtype = 'uint8')

            for i in range(0,min_table):
                lut[i] = 0
            for i in range(min_table,max_table):
                lut[i] = 255 * (i - min_table) / diff_table
            for i in range(max_table, 255):
                lut[i] = 255

            img_median = cv2.medianBlur(img_filt,101)

            img2gray = cv2.cvtColor(img_filt,cv2.COLOR_BGR2GRAY)
            img_median2gray = cv2.cvtColor(img_median,cv2.COLOR_BGR2GRAY)

            diff = cv2.absdiff(img2gray,img_median2gray)
            diff = cv2.LUT(diff,lut)

            ret,thresh = cv2.threshold(diff,40,255,cv2.THRESH_BINARY)
            dilate = cv2.dilate(thresh,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations = 1)
            nlabels,labelimg,contours,gosc = cv2.connectedComponentsWithStats(dilate)

            print(nlabels)
            for d in range(1,nlabels,1):
                x,y,w,h,size = contours[d]
                image_area = w * h
                _x = x - 100
                _y = y - 100
                _w = w + 100
                _h = h + 100

                if _x >= 0:
                    x = _x

                if _y >= 0:
                    y = _y

                if (x+_w) <= img_filt.shape[1]:
                    w = _w

                if (y+_h) <= img_filt.shape[0]:
                    h = _h

                #検出したクラックの中で閾値以上の面積を持つものだけを追加
                if size > 200 and image_area > size:
                    pos.append([x,y,w,h])

            number = len(pos)

            if pos == [] or number == 0:
                cant_detect_dialog = wx.MessageDialog(self,u"クラックの検出ができませんでした。","Can't detect cracks...",style = wx.OK | wx.ICON_ERROR)
                cant_detect_dialog.ShowModal()

            memory = pos

            first_image = cv2.imread(img_adr)
            cv2.rectangle(first_image,(pos[0][0],pos[0][1]),(pos[0][0]+pos[0][2],pos[0][1]+pos[0][3]),(0,0,255),2)
            cv2.putText(first_image,'1',(int(pos[0][0]+(pos[0][2]/2)),int(pos[0][1]+(pos[0][3]/2))),cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,1,(0,0,0),6,cv2.LINE_AA)
            cv2.putText(first_image,'1',(int(pos[0][0]+(pos[0][2]/2)),int(pos[0][1]+(pos[0][3]/2))),cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,1,(random.randint(100,255),random.randint(100,255),random.randint(100,255)),3,cv2.LINE_AA)

            first_drew = first_image
            first_drew = cv2.resize(first_drew,(int(img_width),int(img_height)))
            cv2.imwrite("drew.jpg",first_drew)
            first_detect_image = wx.Image("drew.jpg")
            first_drew_bmp = first_detect_image.ConvertToBitmap()

            dc = wx.ClientDC(viewer_panel)
            dc.Clear()
            bbit = wx.Bitmap(460,460)
            dc.DrawBitmap(bbit,0,0,True)
            dc.DrawBitmap(first_drew_bmp,0,0,True)
            finish_message = wx.MessageDialog(main_panel,u"検出終了\n%d個検出しました。"%len(pos),u"Detecting cracks has finished.",style = wx.OK | wx.ICON_INFORMATION)
            finish_message.ShowModal()

            select_ctrl_panel.Destroy()
            select_ctrl_panel = wx.Panel(self,wx.ID_ANY,pos = (230,460),size = (230,30))
            select_ctrl_panel.SetBackgroundColour("#ffffff")
            self.select_ctrl = wx.SpinCtrl(select_ctrl_panel,wx.ID_ANY,value = "1",min = 1,max = len(pos),size = (230,30))
            self.select_ctrl.Bind(wx.EVT_SPINCTRL,self.select_area_number)

            print("succsess select_ctrl_panel")

            judge_and_make.Destroy()
            judge_and_make = Judge_and_Make(main_panel,memory)

            print("succsess judge_and_make")

        elif img_adr == "":
            undefined = wx.MessageDialog(main_panel,u"画像を選択してください。",u"Undefine image.",style = wx.OK | wx.ICON_EXCLAMATION)
            undefined.ShowModal()

    #指定した番号の検出領域を表示
    def select_area_number(self,event=None):

        global memory
        global img_adr
        global img_width
        global img_height
        global viewer_panel

        pdc = wx.BufferedDC(wx.ClientDC(viewer_panel))

        try:
            # アンチエイリアスをかける
            dc = wx.GCDC(pdc)
        except:
            dc = pdc

        obj = event.GetEventObject()
        pos = memory
        base_image = cv2.imread(img_adr)
        area_number = int(str(obj.GetValue()))

        if pos == []:
            no_area = wx.MessageDialog(self,u"損傷領域の情報がありません",u"No damage area information.",style = wx.OK | wx.ICON_ERROR)
            no_area.ShowModal()
        elif pos != []:
            cv2.rectangle(base_image,(pos[area_number-1][0],pos[area_number-1][1]),(pos[area_number-1][0]+pos[area_number-1][2],pos[area_number-1][1]+pos[area_number-1][3]),(0,0,255),2)

            cv2.putText(base_image,'%d'%area_number,(int(pos[area_number-1][0]+(pos[area_number-1][2]/2)),int(pos[area_number-1][1]+(pos[area_number-1][3]/2))),cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,1,(0,0,0),6,cv2.LINE_AA)
            cv2.putText(base_image,'%d'%area_number,(int(pos[area_number-1][0]+(pos[area_number-1][2]/2)),int(pos[area_number-1][1]+(pos[area_number-1][3]/2))),cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,1,(random.randint(100,255),random.randint(100,255),random.randint(100,255)),3,cv2.LINE_AA)

            drew = base_image
            drew = cv2.resize(drew,(int(img_width),int(img_height)))

            cv2.imwrite("drew.jpg",drew)
            detect_image = wx.Image("drew.jpg")
            drew_bmp = detect_image.ConvertToBitmap()

            dc.Clear()
            bbit = wx.Bitmap(460, 460) #アプリケーション内に埋め込む画像のサイズに変更
            dc.DrawBitmap(bbit,0,0,True)
            dc.DrawBitmap(drew_bmp, 0, 0, True)  #ビットマップ画像をアプリケーションに描画


#ラベル付与用のラジオボックスを表示させるフレーム
class Judge_and_Make(wx.Panel):

    def __init__(self,parent,mem):

        global save_name
        global save_path

        wx.Panel.__init__(self,parent,wx.ID_ANY,pos = (200,490),size = (460,260),style = wx.BORDER_RAISED)
        self.SetBackgroundColour("#888888")
        Static_box_panel = wx.Panel(self,wx.ID_ANY,pos = (0,0),size = (460,210))

        self.determine_Rank = Determine_Rank(Static_box_panel,mem)
        self.determine_Rank.SetBackgroundColour("#888888")
        box = wx.StaticBox(Static_box_panel,wx.ID_ANY,u"クラックのレベル判定")

        layout_determine = wx.StaticBoxSizer(box,wx.VERTICAL)
        layout_determine.Add(self.determine_Rank)

        Static_box_panel.SetSizer(layout_determine)

        button_panel_jm = wx.Panel(self,wx.ID_ANY,pos = (0,210),size = (120,50))
        save_button = wx.Button(button_panel_jm,wx.ID_ANY,u"データセット保存",size = (120,50))

        save_button.Bind(wx.EVT_BUTTON,self.make_dataset_jm)

        layout_buttons = wx.BoxSizer(wx.VERTICAL)
        layout_buttons.Add(save_button,flag = wx.SHAPED | wx.ALIGN_RIGHT)

        button_panel_jm.SetSizer(layout_buttons)

        main_layout_jm = wx.BoxSizer(wx.VERTICAL)
        main_layout_jm.Add(Static_box_panel)
        main_layout_jm.Add(button_panel_jm)

        self.SetSizer(main_layout_jm)

    #検出した分だけラジオボックスを生成する機能
    def make_dataset_jm(self,event):
        self.determine_Rank.make_dataset_dm()



class Determine_Rank(scrl.ScrolledPanel):

    def __init__(self,parent,mem2):

        global img_adr
        global img_size
        global save_path
        global new_pos_set

        scrl.ScrolledPanel.__init__(self,parent,wx.ID_ANY,pos = (10,10),size = wx.Size(430,200))
        self.SetupScrolling()

        self.memory2 = mem2
        self.array_len = 0

        if mem2 != []:
            self.array_len = len(mem2)
            self.radio_box = {}

            button_array = ("Rank 0","Rank 1","Rank 2","Rank 3","Rank 4","Rank 5")

            layout = wx.BoxSizer(wx.VERTICAL)
            for a in range(self.array_len):
                temp_radio = wx.RadioBox(self,wx.ID_ANY,label = "領域" + "%d"%(a+1),pos = (0,10+a*1),choices = button_array,style = wx.RA_HORIZONTAL)
                self.radio_box[str(a)] = temp_radio
                layout.Add(temp_radio)
            self.SetSizer(layout)
            self.Show(True)

    #ラジオボックスから選択されたボタンの情報を読み取り、CSVファイルとして保存する機能
    def make_dataset_dm(self):

        global img_adr
        global img_size
        global save_name
        global save_path
        global attention_name

        head_flag = 0

        if os_type == "nt":
            file_name = img_adr.rsplit("\\",1)
        elif os_type == "posix":
            file_name = img_adr.rsplit("/",1)

        if self.array_len == 0:
            no_labels_dialog = wx.MessageDialog(self,u"データラベルがありません","No label datas",style = wx.OK | wx.ICON_EXCLAMATION)
            no_labels_dialog.ShowModal()

        elif self.array_len != 0:
            final_cofirmation_dialog = wx.MessageDialog(self,u"%sについてのデータセットを保存しますか?"%attention_name[1],"Final Confirmation",style = wx.YES_NO)
            yes_no_select = final_cofirmation_dialog.ShowModal()

            if yes_no_select == wx.ID_YES:

                save_daialog = wx.FileDialog(None,u"ファイルを選択",style = wx.FD_SAVE)

                if save_name != "":
                    save_daialog.SetPath(save_path)

                save_d_signal = save_daialog.ShowModal()
                save_name = save_daialog.GetFilename()
                save_path = save_daialog.GetPath()
                print(save_name)

                if save_d_signal == wx.ID_OK:

                    #CSVファイルに保存するときに、各列の属性を指定
                    col_index = ["#filename","file_size","file_attributes","region_count","region_id","region_shape_attributes","region_attributes"]

                    flag = self.name_redundancy(save_path,attention_name[1])
                    print(flag)
                    if flag == True:
                        redundant_dialog = wx.MessageDialog(self,u"同じ名前の画像がすでに登録されています。\nこのまま上書きしますか？","Name edundancy",style = wx.YES_NO | wx.ICON_EXCLAMATION)
                        redundant_d_signal = redundant_dialog.ShowModal()

                        if redundant_d_signal == wx.ID_YES:

                            csv_register = []
                            t = []

                            with open(save_daialog.GetPath() + ".csv","r") as r_f:
                                file = save_daialog.GetPath() + ".csv"
                                reader = csv.reader(r_f)
                                header = next(reader)
                                for row in reader:
                                    if row != []:
                                        csv_register.append(row)

                            for t in range(len(csv_register),0,-1):
                                if csv_register[t-1][0] == attention_name[1]:
                                    del csv_register[t-1]

                            with open(save_daialog.GetPath() + ".csv","w", newline = '') as w_f:
                                writer = csv.writer(w_f)
                                writer.writerow(col_index)

                            with open(save_daialog.GetPath() + ".csv","a", newline = '') as a_f:
                                writer = csv.writer(a_f)
                                for p in csv_register:
                                    writer.writerow(p)
                                for c in range(self.array_len):
                                    img_size_int = int(img_size)
                                    Rank = self.radio_box[str(c)].GetSelection()
                                    crack_Rank = '{"crack":"%d"}' % Rank
                                    position = '{"name":"rect","x":%d,"y":%d,"width":%d,"height":%d}'%(self.memory2[c][0],self.memory2[c][1],self.memory2[c][2],self.memory2[c][3])
                                    rows = [attention_name[1],img_size_int,'{"Auto:1"}',self.array_len,c,position,crack_Rank]
                                    writer.writerow(rows)

                                print("上書き完了！")

                        elif redundant_d_signal == wx.ID_NO:
                            pass

                    elif flag == False:
                        redundant_dialog = wx.MessageDialog(self,u"保存しました。","Saved",style = wx.OK | wx.ICON_EXCLAMATION)
                        redundant_d_signal = redundant_dialog.ShowModal()
                        with open(save_daialog.GetPath() + ".csv",'a', newline = '') as a_f:
                            file_place = save_daialog.GetPath() + ".csv"
                            print(file_place)
                            writer = csv.writer(a_f)
                            if os.path.getsize(file_place) == 0:
                                writer.writerow(col_index)
                            for c in range(self.array_len):
                                img_size_int = int(img_size)
                                Rank = self.radio_box[str(c)].GetSelection()
                                crack_Rank = '{"crack":"%d"}' % Rank
                                position = '{"name":"rect","x":%d,"y":%d,"width":%d,"height":%d}'%(self.memory2[c][0],self.memory2[c][1],self.memory2[c][2],self.memory2[c][3])
                                rows = [attention_name[1],img_size_int,'{"Auto:1"}',self.array_len,c,position,crack_Rank]
                                writer.writerow(rows)
                            print("yes")

                elif save_d_signal == wx.ID_CANCEL:
                    pass

            elif yes_no_select == wx.ID_NO:
                print("no")

    #同じ名前の画像についてすでにラベルが保存されていた場合に処理を続行するか確認する機能
    def  name_redundancy(self,name,img_name):

        print(os.path.exists(name))

        if os.path.exists(name + ".csv"):
            print("name_redundancy:true")
            file_array = []
            before_name = ""

            with open(name + ".csv","r") as csv_file:
                lines = csv_file.readlines()
                for line in lines:
                    line = line.split(",")
                    column_1_name = line[0]
                    if column_1_name == before_name:
                        pass
                    elif column_1_name != before_name:
                        before_name = line[0]
                        file_array.append(column_1_name)

            redund_flag = img_name in file_array

        else:
            redund_flag = False
            print("name_redundancy:false")

        return redund_flag


#アプリケーションを開始
if __name__ == "__main__":
    print('Application Started.')
    application = wx.App()
    frame = MainFrame()
    frame.Center()
    frame.Show()
    application.MainLoop()
