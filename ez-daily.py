#!/usr/bin/python

import os, sys, re, time, arrow
from requests_html import HTMLSession  #导入requests_html库以爬取页面

session = HTMLSession()
pattern = re.compile('[0-9]{1,2}')  #定义正则表达式


#显示进度条
def view_bar(date, num, sum):
    rate = num / sum
    ss = int(50 * rate)
    a = '#' * ss
    b = '-' * (50 - ss)
    sys.stdout.write(f'\rDate: {date}  [{a}{b}] {rate:.2%}'),
    sys.stdout.flush()


def isLeapYear(year):
    '''
    通过判断闰年，获取年份years下一年的总天数
    :param year: 年份，int
    :return:days_sum，一年的总天数
    '''
    # 断言：年份不为整数时，抛出异常。
    assert isinstance(year, int), "请输入整数年，如 2018"

    if ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)):  # 判断是否是闰年
        # print(year, "是闰年")
        days_sum = 366
        return days_sum
    else:
        # print(year, '不是闰年')
        days_sum = 365
        return days_sum


def DateMonth(year, mon):
    '''
    获取一年的所有日期
    :param year:年份
    :return:某月的日期列表
    '''
    start_date = f'{year}-1-1'
    d = 0
    date_list = []
    days_sum = isLeapYear(int(year))
    while d < days_sum:
        mons = arrow.get(start_date).shift(days=d).format("MM")
        days = arrow.get(start_date).shift(days=d).format("DD")
        mon_now = arrow.now().format("MM")
        day_now = arrow.now().format("DD")
        d += 1
        if int(mons) == int(mon) and int(f'{year}{mons}{days}') <= int(
                f'{year}{mon_now}{day_now}'):
            date_list.append((mons, days))
    return date_list


#获取当前日期
def DateNow():
    year_now = arrow.now().format("YYYY")
    mon_now = arrow.now().format("MM")
    day_now = arrow.now().format("DD")
    return (year_now, mon_now, day_now)


#定义创建分类文件夹的函数，根据传入的年月日参数创建对应文件夹
def mkdir(year, mon, day):
    year = f'{year}年'
    mon = f'{mon}月'
    day = f'{day}日'
    dir_y = os.path.join(dir_paper, year)
    dir_m = os.path.join(dir_y, mon)
    dir_d = os.path.join(dir_m, day)
    if not os.path.isdir(dir_paper):  #检测文件夹是否已存在，是则不再建立文件夹
        os.mkdir(dir_paper)
    if not os.path.isdir(dir_y):  #检测文件夹是否已存在，是则不再建立文件夹
        os.mkdir(dir_y)
    if not os.path.isdir(dir_m):
        os.mkdir(dir_m)
    if not os.path.isdir(dir_d):
        os.mkdir(dir_d)


#定义爬取、生成链接与下载pdf的函数
def paper(year, mon, day):
    timer_start = time.time()  #开始计时
    title = []
    nums = []
    mon = f'{int(mon):0>2d}'
    day = f'{int(day):0>2d}'
    date = f'{year}-{mon}-{day}'
    #根据传入参数生成页面链接 示例：http://paper.people.com.cn/rmrb/html/2021-03/09/nbs.D110000renmrb_01.htm
    r = session.get(
        f'http://paper.people.com.cn/rmrb/html/{year}-{mon}/{day}/nbs.D110000renmrb_01.htm'
    ).html
    #使用css筛选器从页面中查找分页标签 示例："18版：民主政治"
    if int(f'{year}{mon}{day}') >= 20200701 or int(
            f'{year}{mon}{day}') == 20200620:
        pages = r.find('div.swiper-slide > a:nth-child(1)')
    else:
        pages = r.find(
            'div.right_title1,div.right_title2 > div:nth-child(1) > a')
    #如果页面不存在则返回错误提示
    global len_pages
    len_pages = len(pages)
    if not len_pages:
        return f'{date} is not a valid date!'

    mkdir(year, mon, day)  #创建当前日期对应的文件夹

    #将标签进行筛选，并分别以文本形式保存到两个数组
    for page in pages:
        #筛选掉包含关键词"广告"的标签 示例："20版：广告"
        if '广告' not in page.text:
            #将筛选后的标签与序号分别加入数组title与nums 示例："18版：民主政治"
            title.append(re.sub('：', '-', page.text))
            nums.append(f'{int(pattern.findall(page.text)[0]):0>2d}')

    #遍历数组nums，拼接得到下载地址与保存路径
    #示例：http://paper.people.com.cn/rmrb/images/2021-03/09/01/rmrb2021030901.pdf

    for i in range(len(nums)):
        if int(f'{year}{mon}{day}') >= 20200701:
            pdf_url = f'http://paper.people.com.cn/rmrb/images/{year}-{mon}/{day}/{nums[i]}/rmrb{year}{mon}{day}{nums[i]}.pdf'
        else:
            pdf_url = f'http://paper.people.com.cn/rmrb/page/{year}-{mon}/{day}/{nums[i]}/rmrb{year}{mon}{day}{nums[i]}.pdf'
        pdf_path = os.path.join(path_doc, 'PeoplesDaily',
                                f'{year}年/{mon}月/{day}日/{title[i]}.pdf')
        #判断文件是否存在
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 500000:
            with open(pdf_path, 'wb+') as f:  #示例：./2020年/09月/09日/
                f.write(session.get(pdf_url).content)  #下载PDF，保存到文件
        view_bar(date, i + 1, len(nums))
    timer = time.time() - timer_start  #计时结束
    return (f' Total Time: {timer:.2f} s')  #下载成功，返回提示


#使用方法提示
def usage():
    print(f'''Download People's Daily Easily!
          
USAGE: ez-daily [Operation...] [args]
    
Operations:

    -h, --help      Show help options
    -n, <null>      Download today's People's Daily
    -d [date]       Download People's Daily for that day
    -m [month]      Download People's Daily of that month
    
Examples:
    ez-daily
    ez-daily -d 2021 03 10
    ez-daily -m 2020 03
    ''')


if __name__ == '__main__':
    global dir_paper
    path_doc = os.popen('xdg-user-dir DOCUMENTS').read().strip()
    dir_paper = os.path.join(path_doc, 'PeoplesDaily')

    try:
        if len(sys.argv) == 1 or sys.argv[1] == '-n':  #下载今天的人民日报
            date = DateNow()
            print(paper(date[0], date[1], date[2]))
            print(f'Today\'s papers are saved in the folder {dir_paper}')

        elif sys.argv[1] == '-h' or sys.argv[1] == '--help':  #输出帮助
            usage()

        elif sys.argv[1] == '-d' and len(sys.argv) == 5:  #下载指定日期的人民日报
            print(paper(sys.argv[2], sys.argv[3], sys.argv[4]))
            if len_pages:
                print(
                    f'Papers of {sys.argv[2]}-{sys.argv[3]}-{sys.argv[4]} are saved in the folder {dir_paper}'
                )

        elif sys.argv[1] == '-m' and len(sys.argv) == 4:  #下载指定月份的人民日报
            date = DateMonth(f'{sys.argv[2]}', sys.argv[3])
            for i in range(len(date)):
                print(paper(sys.argv[2], date[i][0], date[i][1]))
            print(
                f'Papers of {sys.argv[2]}-{sys.argv[3]} are saved in the folder {dir_paper}'
            )

        else:
            print('Please enter correctly! Input "ez-daily -h" for more help.')
    except:
        print('\nUnknown error! Please recheck and try again!')