# -*- coding: utf-8 -*-
from odoo import api, fields, models


CHINA_CITY_DATA = {
    "北京市": ["北京市"],
    "天津市": ["天津市"],
    "上海市": ["上海市"],
    "重庆市": ["重庆市"],
    "河北省": ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市", "衡水市"],
    "山西省": ["太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市", "吕梁市"],
    "内蒙古自治区": ["呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市"],
    "辽宁省": ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"],
    "吉林省": ["长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市"],
    "黑龙江省": ["哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市", "黑河市", "绥化市"],
    "江苏省": ["南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市", "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市"],
    "浙江省": ["杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市", "金华市", "衢州市", "舟山市", "台州市", "丽水市"],
    "安徽省": ["合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市", "阜阳市", "宿州市", "六安市", "亳州市", "池州市", "宣城市"],
    "福建省": ["福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市", "南平市", "龙岩市", "宁德市"],
    "江西省": ["南昌市", "景德镇市", "萍乡市", "九江市", "新余市", "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市", "上饶市"],
    "山东省": ["济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市", "日照市", "临沂市", "德州市", "聊城市", "滨州市", "菏泽市"],
    "河南省": ["郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市", "漯河市", "三门峡市", "南阳市", "商丘市", "信阳市", "周口市", "驻马店市"],
    "湖北省": ["武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市"],
    "湖南省": ["长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市", "永州市", "怀化市", "娄底市"],
    "广东省": ["广州市", "韶关市", "深圳市", "珠海市", "汕头市", "佛山市", "江门市", "湛江市", "茂名市", "肇庆市", "惠州市", "梅州市", "汕尾市", "河源市", "阳江市", "清远市", "东莞市", "中山市", "潮州市", "揭阳市", "云浮市"],
    "广西壮族自治区": ["南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市", "贺州市", "河池市", "来宾市", "崇左市"],
    "海南省": ["海口市", "三亚市", "三沙市", "儋州市"],
    "四川省": ["成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市", "南充市", "眉山市", "宜宾市", "广安市", "达州市", "雅安市", "巴中市", "资阳市", "阿坝藏族羌族自治州", "甘孜藏族自治州", "凉山彝族自治州"],
    "贵州省": ["贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市"],
    "云南省": ["昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市"],
    "西藏自治区": ["拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市"],
    "陕西省": ["西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市"],
    "甘肃省": ["兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市", "定西市", "陇南市"],
    "青海省": ["西宁市", "海东市"],
    "宁夏回族自治区": ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"],
    "新疆维吾尔自治区": ["乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市"],
    "台湾省": ["台北市", "新北市", "桃园市", "台中市", "台南市", "高雄市"],
    "香港特别行政区": ["香港特别行政区"],
    "澳门特别行政区": ["澳门特别行政区"],
}


class ScPartnerCity(models.Model):
    _name = "sc.partner.city"
    _description = "Partner City"
    _order = "state_id, sequence, name"

    name = fields.Char(required=True, index=True)
    country_id = fields.Many2one("res.country", required=True, index=True, ondelete="restrict")
    state_id = fields.Many2one("res.country.state", required=True, index=True, ondelete="restrict")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("state_city_unique", "unique(state_id, name)", "City name must be unique in a province."),
    ]


class ResPartner(models.Model):
    _inherit = "res.partner"

    sc_city_id = fields.Many2one(
        "sc.partner.city",
        string="城市",
        domain="[('state_id', '=?', state_id)]",
        ondelete="restrict",
    )

    @api.onchange("state_id")
    def _onchange_sc_partner_state_id_clear_city(self):
        City = self.env["sc.partner.city"]
        for partner in self:
            if partner.sc_city_id and partner.sc_city_id.state_id != partner.state_id:
                partner.sc_city_id = False
                partner.city = False
            elif partner.city and partner.state_id:
                matched_city = City.search([
                    ("state_id", "=", partner.state_id.id),
                    ("name", "=", str(partner.city or "").strip()),
                ], limit=1)
                if matched_city:
                    partner.sc_city_id = matched_city
                else:
                    partner.sc_city_id = False
                    partner.city = False
        state_id = self.state_id.id if len(self) == 1 and self.state_id else False
        return {"domain": {"sc_city_id": [("state_id", "=", state_id)] if state_id else [("id", "=", False)]}}

    @api.onchange("sc_city_id")
    def _onchange_sc_partner_city_id(self):
        for partner in self:
            partner._sync_city_from_sc_city()

    def _sync_city_from_sc_city(self):
        for partner in self:
            if partner.sc_city_id:
                partner.city = partner.sc_city_id.name
                partner.state_id = partner.sc_city_id.state_id
                partner.country_id = partner.sc_city_id.country_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_sc_city_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals or {})
        self._prepare_sc_city_vals(vals)
        return super().write(vals)

    @api.model
    def _prepare_sc_city_vals(self, vals):
        city_id = vals.get("sc_city_id")
        if not city_id:
            self._prepare_sc_city_from_standard_vals(vals)
            return
        city = self.env["sc.partner.city"].browse(int(city_id))
        if not city.exists():
            return
        vals.setdefault("city", city.name)
        vals.setdefault("state_id", city.state_id.id)
        vals.setdefault("country_id", city.country_id.id)

    @api.model
    def _prepare_sc_city_from_standard_vals(self, vals):
        city_name = str(vals.get("city") or "").strip()
        state_id = vals.get("state_id")
        if not city_name or not state_id:
            return
        city = self.env["sc.partner.city"].sudo().search([
            ("state_id", "=", int(state_id)),
            ("name", "=", city_name),
        ], limit=1)
        if city:
            vals.setdefault("sc_city_id", city.id)


class ScUserPreferenceInitialization(models.TransientModel):
    _inherit = "sc.user.preference.initialization"

    @api.model
    def apply_user_data_baseline(self):
        super().apply_user_data_baseline()
        self.apply_partner_location_data_baseline()
        return True

    @api.model
    def apply_partner_location_data_baseline(self):
        self._ensure_partner_city_data()
        self._backfill_partner_sc_city_ids()
        return True

    @api.model
    def _ensure_partner_city_data(self):
        china = self.env["res.country"].search([("code", "=", "CN")], limit=1)
        if not china:
            return False
        City = self.env["sc.partner.city"].sudo()
        State = self.env["res.country.state"].sudo()
        for state_name, city_names in CHINA_CITY_DATA.items():
            state = State.search([("country_id", "=", china.id), ("name", "=", state_name)], limit=1)
            if not state:
                continue
            for index, city_name in enumerate(city_names, start=1):
                vals = {
                    "name": city_name,
                    "country_id": china.id,
                    "state_id": state.id,
                    "sequence": index * 10,
                    "active": True,
                }
                rec = City.search([("state_id", "=", state.id), ("name", "=", city_name)], limit=1)
                if rec:
                    rec.write(vals)
                else:
                    City.create(vals)
        return True

    @api.model
    def _backfill_partner_sc_city_ids(self):
        Partner = self.env["res.partner"].sudo()
        City = self.env["sc.partner.city"].sudo()
        partners = Partner.search([
            ("sc_city_id", "=", False),
            ("state_id", "!=", False),
            ("city", "!=", False),
        ])
        updated = 0
        for partner in partners:
            city_name = str(partner.city or "").strip()
            if not city_name:
                continue
            city = City.search([
                ("state_id", "=", partner.state_id.id),
                ("name", "=", city_name),
            ], limit=1)
            if not city:
                continue
            partner.with_context(tracking_disable=True).write({"sc_city_id": city.id})
            updated += 1
        return updated
