from prettytable import PrettyTable
from collections import defaultdict
from win32printing import Printer
from tkinter import messagebox, filedialog, ttk, messagebox
from tkinter import*
from threading import Thread
import datetime, time, os, re, sqlite3,threading
import tkinter.font as tf
import pandas as pd


####选取某时间段内初始时间
date_first = 0
####某时间段购买货物及购买时间
p_q_all = [] 
p_q_time = []
p_q_quanity = []
####全局变量设置
print_times = 0
number_stuff_printer = []
name_stuff = []
tables = []
totalprice = 0
number_transations = 0
conn = sqlite3.connect('.\\stuff.db')

##################################建立数据库及查询表格#######################################
def text_create(name, msg):
    desktop_path = ''  # 新创建的txt文件的存放路径
    full_path = desktop_path + name + '.txt'  # 也可以创建一个.doc的word文档
    with open(full_path, 'w') as file:
        file.write(msg)

time1 = datetime.date.today()
time1_str = datetime.datetime.strftime(time1, '%Y%m%d')
content = time1_str

sql = 'CREATE table IF NOT EXISTS [{0}]'.format(time1_str) + '''(商品条码  INT  NOT NULL,
        商品名称           TEXT    NOT NULL,
        商品单价           INT     NOT NULL,
        售出数量           INT,
        售出时间           TIME);'''
sql_insert = 'INSERT INTO [%s]' % (content)+'''(商品条码, 商品名称, 商品单价, 售出数量, 售出时间) \
              VALUES(?, ?, ?, ?, ?)'''

try:
    conn.execute(sql)
    # print('\n'+'数据库创建成功，等待EXCEL文件转入数据库......'+'\n')
except Exception as es:
    print(es)
c = conn.cursor()


def read_excel():
    data = pd.read_excel('.\\test.xls')
    return data

try:
    read_excel().to_sql('stuff_details', con=conn, if_exists='replace')
    conn.commit()
    # print('EXCEL文件存储入数据库成功，收银软件启动中....')
except Exception as es:
    print(es)
##################################数据库及查询表格结束##########################################


####年月日查询返回值
def find_year(event):
    return(comboxlist_year.get())


def find_month(event):
    return(comboxlist_month.get())


def find_date(event):
    return(comboxlist_date.get())


#####导出文件的文件名字及位置
def export_file():
    if comboxlist_select.get() == '按时间段查询':
        name_all_stuff = []
        desktop_path = ''  # 新创建的txt文件的存放路径
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx")
        ##create dataframe
        str_number = re.findall(r'\d+\.?\d*', Text_qrcode_details.get('0.0', 'end'))
        # print(Text_qrcode_details.get('0.0', 'end').index('无线网卡'))
        name_stuff = re.findall(r'(.[\u4E00-\u9FA5_a-zA-Z]+)', Text_qrcode_details.get('0.0', 'end')[121:])
        number_stuff = re.findall(r'\d+\.?\d*', Text_qrcode_details.get('0.0', 'end')[121:])
        for i in range(len(name_stuff)):
            if i%2 == 0:
                name_all_stuff.append(name_stuff[i])
            else:
                pass
        info_overview = pd.DataFrame({'起始时间': ['{}'.format(str_number[0]+str_number[1]+str_number[2])], \
                                    '结束时间': ['{}'.format(str_number[3]+str_number[4]+str_number[5])], \
                                    '交易笔数':  ['{}'.format(int(str_number[6]))], \
                                    '净交易额':  ['{}'.format(float(str_number[7]))]})
        info_details = pd.DataFrame({'商品名称': name_all_stuff, '销售数量': number_stuff})
        
        ##render dataframe as html
        try:
            writer = pd.ExcelWriter(filename)
            info_overview.to_excel(writer,index=False,sheet_name='营业概况')
            info_details.to_excel(writer,index=False,sheet_name='商品详情')
            writer.save()
            Text_qrcode_details.delete('1.0', 'end')
            Text_qrcode_details.insert('end', '\n'+'文件{}已经保存成功，请及时查阅'.format(filename))
        except Exception as es:
            Text_qrcode_details.delete('1.0', 'end')
            Text_qrcode_details.insert('end', '\n'*2+str(es))
    else:
        pass


####获取所有表格名字并转换成字符串列表
def table_name():
    global tables
    name_tables = []
    name_table = conn.execute('SELECT name from sqlite_master where type="table"')
    table = name_table.fetchall()
    for k in range(len(table)):
        name_tables.append(table[k])
    conn.commit()
    name_tables.remove(('stuff_details',))
    for i in range(len(name_tables)):
        tables.append(''.join(tuple(name_tables[i])))
    return list(set(tables))


####某时间段内物品及总价格列表
def price_quanity_all():
    global p_q_all
    global p_q_time
    global p_q_quanity
    global date_first
    p_q_all = [] 
    p_q_time = []
    p_q_quanity = []
    for i in table_name():
        if ((int(i) >= int(date_first)) & (int(i) <= int(add_zero()))):
            sql_time = 'SELECT 售出时间 FROM [%s]' % (i)
            sql_all = 'SELECT 商品单价, 售出数量 FROM [%s]' % (i)
            sql_quanity = 'SELECT 商品名称, 售出数量 FROM [%s]' % (i)
            #
            p_q_each_time = conn.execute(sql_time)
            p_q_time += p_q_each_time
            #
            p_q_each_all = conn.execute(sql_all)
            p_q_all += p_q_each_all
            #
            p_q_each_quanity = conn.execute(sql_quanity)
            p_q_quanity += p_q_each_quanity
        else:
            pass


####某时间段内售卖总额及分类展示
def price_quanity_all_display():
    # 某时间段内物品及总价格列表
    price_quanity_all()
    totalprice = 0
    number_transations = len(set(p_q_time))
    for i, j in p_q_all:
        totalprice = i*j + totalprice

    # 每日交易分类详情
    res = defaultdict(list)
    for item, price in p_q_quanity:
        res[item].append(price)

    # 显示交易详情
    Text_qrcode_details.insert(
                                'end',
                                '\n'
                                + ' 交易笔数：%d 笔' % (number_transations)
                                + '\n'*2
                                + ' 净交易额：%.2f 元' % (totalprice)
                                + '\n'*3
                                + ' 销售分类'
                                + '\n'
                                + ' ======================'
                                )
    for k, v in res.items():
        Text_qrcode_details.insert(
                                    'end', '\n'*2
                                    + ' {0}'.format(k.strip(' '))
                                    + '：'
                                    + ' '*(10+(4-len(k.strip(' ')))*2-len(str(sum(v))))
                                    + '{0}'.format(sum(v))
                                    + '个'
                                    )


####交易查询（当天、指定）
def statistical_report():
    global tables
    global date_first
    ####设定字体
    ft = tf.Font(family='宋体', size=10, weight=NORMAL)
    Text_qrcode_details.tag_config('tag', foreground='black', font=ft)
    # 清屏
    Text_price_total.delete('1.0', 'end')
    Text_qrcode_details.delete('1.0', 'end')
    #
    if comboxlist_select.get() == '当天日期查询':
        comboxlist_year.current(0)
        comboxlist_month.current(0)
        comboxlist_date.current(0)
        statistical_display(content)
    elif comboxlist_select.get() == '指定日期查询':
        if add_zero() in table_name():
            statistical_display(add_zero())
        else:
            Text_qrcode_details.insert(
                                    'end',
                                    '\n'
                                    + ' 请选择正确的查询日期'
                                    )
    else:
        date_later = add_zero()
        if ((int(date_first) > 20200000) & (date_later != None)):
            if (int(date_first) < int(date_later)):
                Text_qrcode_details.insert( 
                                        'end',
                                        '\n'
                                        " 起始："
                                        +"{}年{}月{}日".format(date_first[0:4], date_first[4:6], date_first[6:8])
                                        + "\n"*2
                                        + " 截止："
                                        + "{}年{}月{}日".format(date_later[0:4], date_later[4:6], date_later[6:8])
                                        + "\n"
                                        + " ======================"
                                        + "\n"
                                        , 'tag'
                                        )
                price_quanity_all_display()
            else:
                Text_qrcode_details.insert(
                                        'end',
                                        '\n'
                                        + ' 起始日期为：{}年{}月{}日'.format(date_first[0:4], date_first[4:6], date_first[6:8])
                                        + '\n'*2
                                        + ' 截止日期需在其之后，请重新输入'
                                        )
        else:
            Text_qrcode_details.insert(
                                        'end',
                                        '\n'
                                        + ' 请正确选择日期'
                                        +'\n'
                                        )


####月和日前面是否需要加零的判断
def add_zero():
    if (comboxlist_month.get() == '月' or comboxlist_date.get() == '日' or comboxlist_year.get() == '年'):
        pass
    else:
        if int(comboxlist_month.get()) < 10:
            if int(comboxlist_date.get()) < 10:
                return(comboxlist_year.get()+'0'+comboxlist_month.get()+'0'+comboxlist_date.get())
            else:
                return(comboxlist_year.get()+'0'+comboxlist_month.get()+comboxlist_date.get())
        else:
            return(comboxlist_year.get()+comboxlist_month.get()+comboxlist_date.get())


####正确选择日期提示信息
def correct_date():
    if (comboxlist_month.get() == '月' or comboxlist_date.get() == '日' or comboxlist_year.get() == '年'):
        Text_price_total.delete('1.0', 'end')
        Text_qrcode_details.delete('1.0', 'end')
        Text_qrcode_details.insert(
                                'end',
                                '\n'
                                + ' '*1
                                + '请正确选择日期'
                                +'\n'
                                )


####选择的时间段交易显示
def statistical_periodoftime():
    global date_first
    if comboxlist_select.get() == '按时间段查询':
        if int(date_first) >= 20200000:
            pass
        else:
            Text_price_total.delete('1.0', 'end')
            Text_qrcode_details.delete('1.0', 'end')
            if add_zero() != None:
                Text_qrcode_details.insert(
                                        'end',
                                        '\n'
                                        + ' 查询起始日期：'
                                        + '{}年{}月{}日'.format(add_zero()[0:4], add_zero()[4:6], add_zero()[6:8])
                                        )
                number_text = re.findall(r'\d+\.?\d*', Text_qrcode_details.get('0.0', 'end'))
                date_first = number_text[0]+number_text[1]+number_text[2]
                comboxlist_date.current(0)
                comboxlist_month.current(0)
                comboxlist_year.current(0)        
                ####
                Text_qrcode_details.insert(
                                        'end',
                                        '\n'*2
                                        + ' 请选择截止日期，然后点击确定获取营业数据'
                                        )
            else:
                pass
    else:
        Text_price_total.delete('1.0', 'end')
        Text_qrcode_details.delete('1.0', 'end')
        Text_qrcode_details.insert(
                                'end',
                                '\n'*1
                                + ' '*1
                                + '请选择“按时间段查询”'
                                )


####当日及查询日期交易显示
def statistical_display(content):
    totalprice = 0
    sql_select = 'SELECT 售出时间 FROM [%s]' % (content)
    sql_price = 'SELECT 商品单价, 售出数量 FROM [%s]' % (content)
    results = conn.execute(sql_select)
    number_transations = len(set(results.fetchall()))
    sales_price = conn.execute(sql_price).fetchall()
    for i, j in sales_price:
        totalprice = i*j + totalprice

    # 每日交易分类详情
    res = defaultdict(list)
    sql_statistical = 'SELECT 商品名称, 售出数量 FROM [%s]' % (content)
    statistical_list = conn.execute(sql_statistical).fetchall()
    for item, price in statistical_list:
        res[item].append(price)

    # 显示交易详情
    Text_qrcode_details.insert(
                                'end',
                                '\n'
                                +' 查询日期：{}年{}月{}日'.format(content[0:4], content[4:6], content[6:8])
                                + '\n'*2
                                + ' 交易笔数：%d 笔' % (number_transations)
                                + '\n'*2
                                + ' 净交易额：%.2f 元' % (totalprice)
                                + '\n'*3
                                + ' 销售分类'
                                + '\n'
                                + ' ===================='
                                , 'tag'
                                )
    for k, v in res.items():
        Text_qrcode_details.insert(
                                    'end', '\n'*2
                                    + ' {0}：'.format(k.strip(' '))
                                    + ' '*(11-(len(k.strip(' '))-2)*2-(len(str(sum(v)))-1))
                                    + '{0}'.format(sum(v))
                                    + '个'
                                    )


####当日交易打印
def statistical_printer(event):
    if comboxlist_select.get() == '指定日期查询' or comboxlist_select.get() == '当天日期查询':
        data = Text_qrcode_details.get('0.0', 'end')
        font_title = {"height": 12,}
        font_text = {"height": 10,} 
        font_printer= {"height": 7,} 
        if len(Text_qrcode_details.get('0.0', 'end')) >1 : 
            with Printer(linegap=1) as printer:
                printer.text(" 解款报表"+'\n', align='left', font_config=font_title)
                printer.text(" 制表人："+' '*2+'085201 生活优品国华店', font_config=font_text)
                printer.text(" 制表时间："+' '*1+(time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime())), font_config=font_text)
                printer.text(" **************************************", font_config=font_text)
                printer.text(data,font_config=font_text)
        else:
            pass
    else:
        if '请正确选择日期' in Text_qrcode_details.get('0.0', 'end'):
            pass
        elif len(Text_qrcode_details.get('0.0', 'end')) >1:
            Text_qrcode_details.delete('0.0', 'end')
            Text_qrcode_details.insert('end', '\n'+' 指定时间段内容过多浪费纸张，选择'+'\n'*2+' “导出文件”导出为EXCEL文档查阅')
        else:
            pass

##    
def delay_clear():
    time.sleep(2)
    focus_QRcode(k) 


####右侧文本框总价格
def total_price(event):
    global number_stuff_printer
    global totalprice
    global name_stuff
    global print_times
    t = threading.Thread(target=delay_clear)
    if (totalprice > 0) and (print_times == 0):
        font_title = {
                        "height": 10,
                    }
        font_text = {
                        "height": 8,
                    }
        with Printer(linegap=2) as printer:
            printer.text("欢迎光临生活优品店"+'\n', align='left', font_config=font_title)
            printer.text("收银员："+' '*13+'085201 生活优品国华店', font_config=font_text)
            printer.text("收银时间："+' '*10+(time.strftime("%Y-%m-%d     %H:%M:%S", time.localtime()))+'\n', font_config=font_text)
            printer.text('************销*******售************'+'\n', font_config=font_title)
            printer.text(' '*5+'货号'+' '*13+'单价'+' '*2+'数量'+' '*2+'折扣'+'\n', font_config=font_title)
            for i in range(len(number_stuff_printer)):
                printer.text(number_stuff_printer[0][0]+' '*6+number_stuff_printer[0][1]+' '*6+number_stuff_printer[0][2]+' '*10+number_stuff_printer[0][3], font_config=font_text)
                printer.text('商品名称：'+name_stuff[0]+'\n', font_config=font_text)
                s_name = (number_stuff_printer[0][0], name_stuff[0], number_stuff_printer[0][1], number_stuff_printer[0][2], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                conn.execute(sql_insert, (s_name))
                conn.commit()
                del number_stuff_printer[0]
                del name_stuff[0]
            printer.text('*********************************'+'\n', font_config=font_text)
            printer.text('合计：'+' '*4 + '%.2f' % (totalprice)+' '*1+'元', font_config=font_title)
            print_times = 1
            t.start()    
    else:
        stuff_number = []  # 数量
        data_price = []  # 商品单价
        discount_price = []  # 折扣
        result = []  # 计算出的总价格
        # 正则表达式取出文本框内读取内容中的中文 *******商品名称中文名不能有空格*******
        name_stuff = re.findall(r'(.[\u4E00-\u9FA5_a-zA-Z]+)', Text_qrcode_details.get('0.0', 'end'))
        # 正则表达式取出文本框内读取内容中的数字项
        str_number = re.findall(r'\d+\.?\d*', Text_qrcode_details.get('0.0', 'end'))
        for j in range(len(str_number)):
            ret = str_number[0:4]
            if ret == []:
                pass
            else:
                try:
                    number_stuff_printer.append(ret)
                    data_price.append(float(ret[1]))
                    stuff_number.append(int(ret[2]))
                    discount_price.append(float(ret[3]))
                    result = map(lambda x, y, z: x*y*z, stuff_number, data_price, discount_price)
                except Exception as es:
                    Text_price_total.insert('end', es)
            for i in ret:
                str_number.remove(i)
        list_result = list(result)
        totalprice = sum(list_result)
        Text_price_total.delete('1.0', 'end')
        #######总价格显示文本框
        x = PrettyTable(align='c')
        x = PrettyTable(border=False, header=False, padding_width=2)
        ft = tf.Font(family='微软雅黑', size=13, weight=tf.BOLD)
        x.add_row(['\n'+' '*4+'%.2f 元' % totalprice])
        Text_price_total.tag_config('tag', foreground='red', font=ft)
        Text_price_total.insert('insert', str(x), 'tag')
        Text_price_total.update()
        price_number = re.findall(r'\d+\.?\d*',Text_price_total.get('0.0', 'end'))
        if float(price_number[0]) ==0:
            Text_price_total.configure(state='normal')
            Text_qrcode_details.configure(state='normal')
        else:
            Text_price_total.configure(state='disable')
            Text_qrcode_details.configure(state='disable')


#  商品名称列表
def code_list():
    sql_stuff_details = '''SELECT 商品条码 FROM stuff_details'''
    results = conn.execute(sql_stuff_details)
    return(results.fetchall())


#  商品扫码提示
def callback(event):
    cursor = conn.execute("SELECT 商品条码, 商品名称, 价格, 数量, 折扣 FROM stuff_details")
    every_stuff = cursor.fetchall()
    x = PrettyTable(border=False, header=False, padding_width=4)
    if '' == Entry_QRcode.get():
        messagebox.showerror('错误', '请输入商品条码')
        Entry_QRcode.delete(0, 'end')
    elif tuple([int(Entry_QRcode.get())]) not in code_list():
        messagebox.showerror('错误', '未能找到该商品')
        Entry_QRcode.delete(0, 'end')
    else:
        ft = tf.Font(family='微软雅黑', size=11, weight=NORMAL)
        for i in every_stuff:
            if str(i[0]) == Entry_QRcode.get(): 
                list_i = list(i)
                list_i[1] = ' '*(16-len(list_i[1])*2)+list_i[1]+' '*(16-len(list_i[1])*2)
                list_i[3] = ' '*4+str(list_i[3])+' '*4
                x.add_row(list_i)
                Text_qrcode_details.tag_config('tag', foreground='blue', font=ft)
                Text_qrcode_details.insert('insert', '\n'+str(x)+'\n', 'tag')
                Text_qrcode_details.update()
                Entry_QRcode.delete(0, 'end')
            else:
                pass
                

# 按F2聚焦到扫码框
def focus_QRcode(event):
    global date_first
    global p_q_all
    global p_q_time
    global p_q_quanity
    global name_stuff
    global totalprice
    global number_transations
    global number_stuff_printer
    global print_times
    ##时间复位
    comboxlist_year.current(0)
    comboxlist_month.current(0)
    comboxlist_date.current(0)
    ##文本框及价格框状态复位
    Text_price_total.configure(state='normal')
    Text_qrcode_details.configure(state='normal')
    ##数据复位
    date_first = 0
    totalprice = 0
    print_times = 0
    number_transations = 0
    p_q_all = [] 
    p_q_time = []
    name_stuff = []
    p_q_quanity = [] 
    number_stuff_printer = []
    ##清屏
    Text_price_total.delete('1.0', 'end')
    Text_qrcode_details.delete('1.0', 'end')
    ##聚焦扫码
    Entry_QRcode.focus_set()


####退出程序前提示
def exit_programm():
    if messagebox.askokcancel("收银系统", "确定需要退出吗"):
        root.quit()

####程序窗口设置####
root = Tk()
# 设置窗口大小
winWidth = 640
winHeight = 640
# 屏幕分辨率
screenWidth = root.winfo_screenwidth()
screenHeight = root.winfo_screenheight()
x = int((screenWidth - winWidth) / 2)
y = int((screenHeight - winHeight) / 2)
# 设置窗口初始位置在屏幕居中
root.geometry("%sx%s+%s+%s" % (winWidth, winHeight, x, y))
# 设置窗口图标
root.iconbitmap(".\\Clipboard.ico")
# 设置主窗口标题
root.title('  简方收银')
# 设置窗口宽高固定
root.resizable(0, 0)
# 设定程序快捷键
root.bind('<F1>', total_price)
root.bind('<Escape>', focus_QRcode)
root.bind('<Control-F4>', statistical_printer)
root.protocol("WM_DELETE_WINDOW", exit_programm)


'''创建分区'''
# 在主面板上划分区域
QRcode_Frame = Frame(root)  # 创建 <二维码列表分区>
stuffname_Frame = Frame(root)
stuff_details_Frame = Frame(root)  # 创建 <商品标签分区>
hotkey_Frame = Frame(root)  # 创建 <快捷键提示分区>
button_Frame = Frame(root)

####Frame在主控件上的布局
QRcode_Frame.pack(fill='x', expand='no')
button_Frame.pack(fill='x', expand='no')
stuffname_Frame.pack(fill='x', expand='no')
stuff_details_Frame.pack(fill='both', expand='yes')
hotkey_Frame.pack(pady=5)

####扫码框显示
label_QRcode = ttk.Label(QRcode_Frame, text='条码扫描')
label_QRcode.pack(padx=5, pady=10, side='left')
Entry_QRcode = ttk.Entry(QRcode_Frame)
Entry_QRcode.pack(padx=10, side='left')
Entry_QRcode.bind('<Return>', callback)
Entry_QRcode.focus_set()

####商品显示
ft = tf.Font(family='微软雅黑', size=10, weight=tf.BOLD)
label_stuffname = ttk.Label(
                        stuffname_Frame, text=
                        '|'
                        +' '*11
                        +'商品条码'
                        +' '*11
                        +'|'
                        +' '*12
                        +'商品名称'
                        +' '*12
                        +'|'
                        +' '*6
                        + '价格'
                        +' '*6
                        +'|'
                        +' '*4
                        + '数量'
                        +' '*4
                        +'|'
                        +' '*3
                        + '折扣'
                        +' '*4
                        +'|'
                        +' '*11
                        + '总计金额'
                        , font=ft
                        , foreground='dimgray'
                     )
label_stuffname.pack(padx=1, side='left')

####文本框中显示内容
Text_qrcode_details = Text(stuff_details_Frame, width=70)
Text_qrcode_details.pack(padx=5, pady=4, side='left',fill='y')
####价格框中内容
Text_price_total = Text(stuff_details_Frame, width=18)
Text_price_total.pack(side='right', padx=2, pady=4, fill='y')

# 按钮栏显示
varDict = locals()
for i in range(1, 5):
    varDict['comvalue_'+str(i)] = StringVar()
# 显示当前日期、指定日期及指定时间段查询
comboxlist_select = ttk.Combobox(button_Frame, width=15, textvariable=comvalue_1)
select = ['当天日期查询', '指定日期查询', '按时间段查询']
comboxlist_select.pack(padx=5, pady=20, side='left')
comboxlist_select["values"] = (select)
comboxlist_select.current(0)   # 选择第一个
# 显示'年'
comboxlist_year = ttk.Combobox(button_Frame, width=4, textvariable=comvalue_2)
comboxlist_year.pack(side='left')
year = []
for i in range(2020, 2050):
    year.append(i)
year.insert(0, '年')
comboxlist_year["values"] = (year)
comboxlist_year.current(0)   # 选择第一个
comboxlist_year.bind("<<ComboboxSelected>>", find_year)
#  显示'月'
comboxlist_month = ttk.Combobox(button_Frame, width=2, textvariable=comvalue_3)
comboxlist_month.pack(padx=10, side='left')
month = []
for j in range(1, 13):
    month.append(j)
month.insert(0, '月')
comboxlist_month['values'] = (month)
comboxlist_month.current(0)   # 选择第一个
comboxlist_month.bind("<<ComboboxSelected>>", find_month)
#  显示'日'
comboxlist_date = ttk.Combobox(button_Frame, width=2, textvariable=comvalue_4)
comboxlist_date.pack(side='left')
date = []
for k in range(1, 32):
    date.append(k)
date.insert(0, '日')
comboxlist_date['values'] = (date)
comboxlist_date.current(0)  # 选择第一个
comboxlist_date.bind("<<ComboboxSelected>>", find_date)
# ‘至’按钮
Todate_button = ttk.Button(button_Frame, text='至', width=2, command=statistical_periodoftime)
Todate_button.pack(padx=10, side='left')
# 确定按钮
forsure_button = ttk.Button(button_Frame, text='确定', width=4, command=statistical_report)
forsure_button.pack(padx=15, side='left')
# 导出按钮
export_button = ttk.Button(button_Frame, text='导出文件', width=7, command=export_file)
export_button.pack(padx=35, side='right')


####标签栏显示
ft = tf.Font(family='微软雅黑', size=9, weight=NORMAL)
s_time = time.strftime("%Y-%m-%d", time.localtime())
label_hotkey = ttk.Label(
                        hotkey_Frame, text=' ESC：清屏重置并返回扫码'
                        + ' '*4
                        + '|'
                        + ' '*4
                        + 'F1：总金额及打印小票'
                        + ' '*4
                        + '|'
                        + ' '*4
                        + 'Ctrl+F4：当天及指定日期报表打印'
                        + ' '*4
                        + '|'
                        + ' '*4
                        + s_time
                        , font=ft
                     )
label_hotkey.pack(side='bottom')

####今天表格如果没有导入或者数据导入错误，文本框内显示提示
compare_time = time.strftime("%Y%m%d", time.localtime())
if compare_time not in table_name():
    ft = tf.Font(family='微软雅黑', size=12, weight=NORMAL)
    Text_qrcode_details.tag_config('tag', foreground='black', font=ft)
    Text_qrcode_details.insert(
                        'end',
                        '\n'
                        + ' 请点击右侧更新按键，完毕后再次运行本收银程序'
                        , 'tag'
                        )
 
####主程序循环
root.mainloop()
