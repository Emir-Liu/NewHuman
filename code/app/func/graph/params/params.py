"""
默认参数
"""

# 默认业务代码映射
business_mapping_default = {"个人信息维护":"personalcustomer360","个人回单打印":"receiptprintmenupersonal","个人明细查询":"receiptprintmenupersonal","个人智能存款维护":"personaldepositmaintenance","个人账户开户":"openaccountmenu","个人账户查询":"personalacctount360","个人账户转账":"personaltransfer","主卡销户":"personalacctclose","主卡销附属卡":"mastercardCloseSubsidiary","互转记录查询":"eachothertransferrecordservice","人寿保险购买":"insuranceBuy","余额查询":"remainingsumservice","保险风险评估":"riskLevelByInsurance","卡折激活":"activemediamenu","卡正常更换":"changecard","吞卡领取登记":"retaincardregister","基金交易流水查询":"queryFoundationTranserial","基金定投管理":"autoinvestmentmanage","基金客户信息维护":"foundationcustinfomaintain","基金当日可撤单":"foundationcancel","基金申购/认购/定投购买":"foundationbuy","基金确认单打印":"foundationBillsPrinter","基金解约":"fundTermination","基金账户信息查询":"queryFoundationInfo","基金账户销户":"foundationclose","基金银行账号变更":"foundationAccountChange","基金风险评估":"foundationriskassessment","大额存单兑付":"cashbigdrm","大额存单查询":"querybigdrm","大额存单购买":"openbigdrm","存折补登":"autoservicepassbook","定期存款开户":"openfixeddeposit","定期存款销户":"closefixeddeposit","密码修改":"setpasswordCard","密码解锁":"passwordunlockCard","密码重置":"passwordresetCard","对公余额查询":"receiptprintmenu","对公回单打印":"receiptprintmenu","对公明细查询":"receiptprintmenu","广播电视费缴费":"radioandtelevisionfeesservice","延时转账撤销":"revocationtransfer","当日保单撤回":"insuranceCancel","我的保单":"insurancePolicy","我的基金":"myfoundation","我的持仓":"myposition","手机银行登录设备维护":"phonelogindevchange","挂失业务":"accountlost","挂失补发":"lostaftertreatment","挂失解挂":"lostaftertreatment","挂失销户":"lostaftertreatment","水费缴费":"waterfeesservice","溢缴款转账支取":"overpaytrsdrawmenu","燃气费缴费":"gasfeesservice","现金取款预约业务":"withdraworder","理财购买":"financialbuy","理财风险评估":"riskassessment","生活缴费记录查询":"paythefeesrecordservice","申领实体卡":"entitycardapplyidcard","电子现金圈提":"electroniccashunload","电子现金销户":"electroniccashclose","电子银行个人签约":"ebanksignservice","电子银行个人签约维护":"savesignservice","电费缴费":"electricfeesservice","综合签约":"signservice","综合解约":"unsignservice","缴费综合签约":"paysignservice","缴费综合解约":"payunsignservice","自动还款管理":"repaymentmenu","补登对账簿":"autoservicepassbook","账户等级调整":"changeacctlevel","账户解绑/绑定":"acctbindandunbind","贵金属购买/预订":"noblemetals","贷记卡密码修改":"modifypasswordmenu","贷记卡密码重置":"resetpassswordmenu","贷记卡挂失":"debitlossidcard","贷记卡查询附卡":"querysupplecard","贷记卡激活":"debitactivemenu","贷记卡申请进度查询":"applyprogress","贷记卡补卡申请":"debitcardapplyidcard","贷记卡账单信息查询":"querybillinfo","贷记卡转账还款":"transbyrepaymenu","银企对账":"bankreconciliation","银证互转":"banksecurityeachothertransferservice","长期不动户激活/销户":"hangingacctmenu","附属卡销户":"subsidiarycardclose"}

# 默认意图映射
intent_mapping_default = {
    "业务办理": "business",
    "咨询": "inquiry",
    "拒识": "reject",
    "敏感词": "sensitive_word",
    "闲聊": "chitchat",
    "防注入": "anti_injection",
}

# 默认记忆轮次
num_history_default = 3

# 知识库-业务描述-知识库-检索默认参数
business_des_kb_top_k_default = 5
business_des_kb_id_default = "1e3fd9e0-a7f7-4566-ada3-abdda5db23d8"

# 知识库-业务数据-知识库-检索默认参数
business_data_kb_top_k_default = 5
business_data_kb_id_default = "64ffd86d-63c6-4e65-b09f-21f6988754d0"

# 知识库-咨询/QA-检索默认参数（inquiry_kb_id 指向咨询专用 QA 知识库，勿留空）
inquiry_kb_top_k_default = 5
inquiry_kb_id_default = "7e221cae-b5a3-4b09-80e8-d0b11ea53ce9"  # 必填：咨询专用 QA 知识库 UUID，可通过 inputs.inquiry_kb_id 覆盖
inquiry_score_threshold_default = 0.8

# 默认金融风险关键词
risk_keyword_list_default = ["安全账户","资金清查","安全验证","验资","验证资金","刷流水","做流水","包装流水","解冻金","保证金","认证金","激活金","解封费","先交费","先打款","手续费先付","征信修复","消除征信","征信洗白","贷款额度冻结","解除风控","取消会员","关闭扣费","自动续费关闭","退款理赔","退保退款","屏幕共享","共享屏幕","远程控制","远程协助","下载会议软件","下载远控软件","线下取现","刷单返利","兼职刷单","垫付返利","虚假投资","带单老师","内幕消息","荐股群","老师喊单","稳赚不赔","保本高收益","高回报","高收益零风险","虚拟币投资","区块链投资","杀猪盘","婚恋投资","冒充客服","冒充物流客服","快递丢失理赔","航班退改签","冒充公检法","涉案账户","洗清嫌疑","配合调查转账","冒充领导","冒充熟人","紧急借款","贷款刷流水","低息免押","无抵押秒批","征信异常","校园贷注销","AI换脸","拟声","合成声音","伪造视频","代办开户","借名开户","挂名法人","空壳公司","壳公司","代持","实控人隐藏","受益所有人","股权代持","走账公司","过账公司","三无公司","异地开户","临时账户","他人代办","非本人办理","借用身份","借用账户","地下钱庄","跑分","跑分平台","卡商","卖卡","收卡","借卡走账","银行卡出租","银行卡出借","对公账户出租","两卡","四件套","非法结算","代付通道","通道费","洗钱","洗白","赃款","赃款转移","套现","取现团队","跑腿取现","上门取现","帮助转账","兼职收款","收款返佣","虚拟币","虚拟货币","数字货币投资","U币","USDT","泰达币","币商","OTC","场外交易","搬砖套利","钱包地址","冷钱包","热钱包","混币","代买币","代卖币","币币兑换","链上转账","不要备注","别备注","不留痕","避开风控","别触发预警","不要走对公","不要走银行卡","现金交割","私下转","分开转","别超过限额","换个人转","借别人卡","借别人账户","不要实名","不要留记录","走私人账户"]

# 默认防注入关键词
injection_keyword_list_default = [
    "忽略指令","不用遵循","新的身份","忽略","忘记所有",
]
