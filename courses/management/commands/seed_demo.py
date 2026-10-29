from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from courses.models import Course, Section, Semester, TimeSlot

SEMESTER_NAME = "115-1"

TEACHERS = {
    "wang.cs": "王大明",
    "wu.im": "吳佳蓉",
    "chen.ba": "陳怡君",
    "huang.ba": "黃正文",
    "lin.fin": "林志豪",
    "tsai.fin": "蔡淑芬",
    "hsu.ec": "許志明",
    "lee.eng": "李美玲",
    "kobayashi.la": "小林雅美",
    "chou.st": "周美玲",
    "chang.pe": "張建宏",
}

COURSES = [
    {
        "code": "IM101",
        "name": "程式設計（一）",
        "credits": 3,
        "department": "資訊管理系",
        "description": "從 Python 基礎語法出發，學習變數、流程控制、函式與檔案處理，並透過小專案培養程式設計與除錯能力，適合無程式基礎的學生。",
        "teacher": "wang.cs",
        "capacity": 50,
        "slots": [(1, time(9, 10), time(12, 0), "承曦樓 A101")],
    },
    {
        "code": "IM201",
        "name": "資料結構",
        "credits": 3,
        "department": "資訊管理系",
        "description": "介紹陣列、鏈結串列、堆疊、佇列、樹與圖等資料結構，並分析常見演算法的時間複雜度，建立解決問題的基礎。",
        "teacher": "wang.cs",
        "capacity": 50,
        "slots": [(2, time(9, 10), time(12, 0), "承曦樓 A102")],
    },
    {
        "code": "BA101",
        "name": "管理學",
        "credits": 3,
        "department": "企業管理系",
        "description": "探討組織管理的基本概念，包括規劃、組織、領導與控制四大功能，並以企業案例討論管理決策與實務應用。",
        "teacher": "chen.ba",
        "capacity": 60,
        "slots": [(3, time(9, 10), time(12, 0), "行政大樓 B201")],
    },
    {
        "code": "FN101",
        "name": "財務管理",
        "credits": 3,
        "department": "財務金融系",
        "description": "介紹財務管理核心觀念，涵蓋財務報表分析、貨幣時間價值、資本預算與風險報酬，建立企業財務決策能力。",
        "teacher": "lin.fin",
        "capacity": 50,
        "slots": [(4, time(9, 10), time(12, 0), "行政大樓 C301")],
    },
    {
        "code": "LA101",
        "name": "商用英文",
        "credits": 2,
        "department": "應用外語系",
        "description": "以商用情境練習英語聽力與口說，包含簡報、會議、客戶溝通與書信往來，強化職場英語溝通能力。",
        "teacher": "lee.eng",
        "capacity": 30,
        "slots": [(2, time(13, 10), time(15, 0), "語言中心 D401")],
    },
    {
        "code": "PE101",
        "name": "體育（籃球）",
        "credits": 1,
        "department": "體育室",
        "description": "透過籃球基本動作、戰術演練與分組比賽，培養規律運動習慣、團隊合作與運動精神。",
        "teacher": "chang.pe",
        "capacity": 40,
        "slots": [(3, time(15, 10), time(17, 0), "體育館")],
    },
    {
        "code": "IM102",
        "name": "計算機概論",
        "credits": 3,
        "department": "資訊管理系",
        "description": "介紹電腦硬體、作業系統、網路與資訊安全的基本概念，建立資訊科技素養與應用能力。",
        "teacher": "wang.cs",
        "capacity": 55,
        "slots": [(1, time(13, 10), time(16, 0), "承曦樓 A103")],
    },
    {
        "code": "IM202",
        "name": "資料庫管理",
        "credits": 3,
        "department": "資訊管理系",
        "description": "學習關聯式資料庫設計、SQL 查詢、正規化與交易管理，並透過實作建立資料庫應用。",
        "teacher": "wang.cs",
        "capacity": 45,
        "slots": [(2, time(15, 10), time(18, 0), "承曦樓 A104")],
    },
    {
        "code": "IM301",
        "name": "網頁程式設計",
        "credits": 3,
        "department": "資訊管理系",
        "description": "從 HTML、CSS 到 JavaScript 與後端整合，實作響應式網站與互動功能。",
        "teacher": "wu.im",
        "capacity": 40,
        "slots": [(4, time(13, 10), time(16, 0), "承曦樓 A105")],
    },
    {
        "code": "BA102",
        "name": "行銷管理",
        "credits": 3,
        "department": "企業管理系",
        "description": "介紹市場區隔、目標市場、定位與行銷組合，並透過案例分析擬定行銷策略。",
        "teacher": "chen.ba",
        "capacity": 60,
        "slots": [(5, time(9, 10), time(12, 0), "行政大樓 B202")],
    },
    {
        "code": "BA201",
        "name": "組織行為",
        "credits": 3,
        "department": "企業管理系",
        "description": "探討個人、團隊與組織層次的行為，涵蓋動機、領導、溝通與組織文化。",
        "teacher": "huang.ba",
        "capacity": 50,
        "slots": [(5, time(13, 10), time(16, 0), "行政大樓 B203")],
    },
    {
        "code": "FN102",
        "name": "會計學（一）",
        "credits": 3,
        "department": "財務金融系",
        "description": "從會計循環出發，學習分錄、過帳、試算表與財務報表編製，奠定會計基礎。",
        "teacher": "lin.fin",
        "capacity": 60,
        "slots": [(1, time(9, 10), time(12, 0), "行政大樓 C302")],
    },
    {
        "code": "FN201",
        "name": "投資學",
        "credits": 3,
        "department": "財務金融系",
        "description": "介紹股票、債券與衍生性商品，學習風險報酬衡量、投資組合與資產配置。",
        "teacher": "tsai.fin",
        "capacity": 45,
        "slots": [(3, time(13, 10), time(16, 0), "行政大樓 C303")],
    },
    {
        "code": "EC101",
        "name": "經濟學",
        "credits": 3,
        "department": "國際商務系",
        "description": "介紹供需、市場均衡、消費者行為與總體經濟指標，培養經濟分析能力。",
        "teacher": "hsu.ec",
        "capacity": 60,
        "slots": [(4, time(9, 10), time(12, 0), "行政大樓 E201")],
    },
    {
        "code": "LA102",
        "name": "日文（一）",
        "credits": 2,
        "department": "應用外語系",
        "description": "從五十音與基礎文法開始，練習日常會話、聽力與簡單閱讀，建立日語基礎。",
        "teacher": "kobayashi.la",
        "capacity": 30,
        "slots": [(5, time(10, 10), time(12, 0), "語言中心 D402")],
    },
    {
        "code": "LA201",
        "name": "英文寫作",
        "credits": 2,
        "department": "應用外語系",
        "description": "練習段落結構、論證與商用書信寫作，強化英文表達與書面溝通能力。",
        "teacher": "lee.eng",
        "capacity": 30,
        "slots": [(4, time(15, 10), time(17, 0), "語言中心 D403")],
    },
    {
        "code": "ST101",
        "name": "統計學",
        "credits": 3,
        "department": "企業管理系",
        "description": "介紹敘述統計、機率分布、估計與假設檢定，並以軟體實作資料分析。",
        "teacher": "chou.st",
        "capacity": 60,
        "slots": [(2, time(13, 10), time(16, 0), "行政大樓 B204")],
    },
    {
        "code": "PE102",
        "name": "體育（羽球）",
        "credits": 1,
        "department": "體育室",
        "description": "學習羽球基本動作、規則與雙打戰術，培養運動習慣與團隊合作。",
        "teacher": "chang.pe",
        "capacity": 40,
        "slots": [(5, time(15, 10), time(17, 0), "體育館")],
    },
]


class Command(BaseCommand):
    help = "建立可加退選的範例學期、教師、課程與時段（可重複執行）。"

    def handle(self, *args, **options):
        now = timezone.now()
        semester, _ = Semester.objects.update_or_create(
            name=SEMESTER_NAME,
            defaults={
                "is_active": True,
                "enroll_start": now - timedelta(days=7),
                "enroll_end": now + timedelta(days=30),
            },
        )
        other_active = Semester.objects.filter(is_active=True).exclude(pk=semester.pk)
        if other_active.exists():
            self.stdout.write(self.style.WARNING(
                "注意：另有啟用中的學期 "
                + "、".join(other_active.values_list("name", flat=True))
                + "，課程列表預設會顯示名稱最大的學期。"
            ))

        user_model = get_user_model()
        teachers = {}
        for username, display_name in TEACHERS.items():
            teacher, created = user_model.objects.get_or_create(
                username=username,
                defaults={"first_name": display_name},
            )
            if created:
                teacher.set_unusable_password()
                teacher.save(update_fields=["password"])
            Profile.objects.update_or_create(
                user=teacher,
                defaults={"role": Profile.Role.TEACHER},
            )
            teachers[username] = teacher

        for spec in COURSES:
            course, _ = Course.objects.update_or_create(
                code=spec["code"],
                defaults={
                    "name": spec["name"],
                    "credits": spec["credits"],
                    "department": spec["department"],
                    "description": spec["description"],
                },
            )
            section, _ = Section.objects.update_or_create(
                course=course,
                semester=semester,
                defaults={
                    "teacher": teachers[spec["teacher"]],
                    "capacity": spec["capacity"],
                },
            )
            for weekday, start_time, end_time, location in spec["slots"]:
                TimeSlot.objects.update_or_create(
                    section=section,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time,
                    defaults={"location": location},
                )
            self.stdout.write(
                f"  {course.code} {course.name}（{course.credits} 學分）"
                f" · {section.teacher.first_name} · 名額 {section.capacity}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"完成：學期 {semester.name} 已開放加退選，共 {len(COURSES)} 門課程。"
        ))
