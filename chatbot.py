from flask import Flask, request, abort
import os
import psycopg2

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    ButtonsTemplate, CarouselColumn, CarouselTemplate, 
    BubbleContainer, CarouselContainer, BoxComponent, TextComponent, ButtonComponent,
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, FlexSendMessage,
    PostbackAction, PostbackTemplateAction
)

app = Flask(__name__)

# 環境変数取得
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
DATABASE_URL = os.environ.get('DATABASE_URL')

line_bot_api = LineBotApi(CACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
    
# Pythonでは呼び出す行より上に記述しないとエラーになる

# リストをn個ずつのサブリストに分割する
# l : リスト
# n : サブリストの要素数
def split_list(l, n):
    for idx in range(0, len(l), n):
        yield l[idx:idx + n]

# 窓口リストを表示する関数
def window_list_flex(db):
    db.append(
        )
    db_column = list(split_list(db, 10))

    contents_carousel = []
    for dbcol in db_column:
        contents_button = []
        for row in dbcol:
            contents_button.append(
                ButtonComponent(
                    style = 'link',
                    height = 'sm',
                    action = PostbackAction(
                        label = str(row[3])[:40],
                        data = 'callback',
                        text = '窓口ID:' + str(row[0])
                    )
                )
            )
        contents_carousel.append(
            BubbleContainer(
                header = BoxComponent(
                    layout = 'vertical',
                    contents = [ 
                        TextComponent(
                            text = '窓口を選択してください',
                            weight = 'bold',
                            color = '#333333',
                            size = 'xl'
                        )
                    ]
                ),
                body = BoxComponent(
                    layout = 'vertical',
                    contents = contents_button
                )
            )
        )
        
    return CarouselContainer(contents=contents_carousel)

# 窓口の情報を出力
def window_info(db):
    result = db[0][4] + "\n"\
        + db[0][5] + "\n"\
        + db[0][6] + "\n"\
        + db[0][7]
    return result

# ブラウザでherokuにアクセスした場合の処理
@app.route("/")
def hello_world():
    return "hello world!"

# LINEからメッセージを受け取った場合の処理
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# データベースの表の出力
@app.route("/database")
def database():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT * FROM window_list ORDER BY Id ASC")
            db = curs.fetchall()
            result = "<table>\
             <tr>\
              <th>Id</th>\
              <th>Category</th>\
              <th>Number</th>\
              <th>Soudan_name</th>\
              <th>Soudan_content</th>\
              <th>Window_name</th>\
              <th>Tel</th>\
              <th>Business_hours</th>\
              <th>Subcategory</th>\
              <th>Timestamp</th>\
             </tr>"
            for row in db: 
                result += "<tr>\
                    <td>" + str(row[0]) + "</td>\
                    <td>" + str(row[1]) + "</td>\
                    <td>" + str(row[2]) + "</td>\
                    <td>" + str(row[3]) + "</td>\
                    <td>" + str(row[4]) + "</td>\
                    <td>" + str(row[5]) + "</td>\
                    <td>" + str(row[6]) + "</td>\
                    <td>" + str(row[7]) + "</td>\
                    <td>" + str(row[8]) + "</td>\
                    <td>" + str(row[9]) + "</td>\
                    </tr>"
            result += "</table>"
    return result

# フォローイベントの場合の処理
@handler.add(FollowEvent)
def handle_follow(event):
    profile = line_bot_api.get_profile(event.source.user_id)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=profile.display_name + "さん、はじめまして！\n" +
        "友だち追加ありがとうございます。福島温泉情報bot（仮）です。\n" +
        "温泉の情報を探したい場合は、まずは「温泉を探す」をタップしてください。")
    )

# メッセージイベントの場合の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    content = event.message.text # メッセージの内容を取得する
   
    if content in ['温泉を探す']:
        carousel_columns = [
            CarouselColumn(
                text='希望する地方を選択してください',
                title='会津で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津',
                        data='callback',
                        text='会津'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する地方を選択してください',
                title='中通りで検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り',
                        data='callback',
                        text='中通り'
                    )
                ]
            ),
            CarouselColumn(
                text='希望する地方を選択してください',
                title='浜通りで検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り',
                        data='callback',
                        text='浜通り'
                    )
                ]
            ),
            CarouselColumn(
                text='希望する地方を選択してください',
                title='希望なし',
                actions=[
                    PostbackTemplateAction(
                        label='場所なし',
                        data='callback',
                        text='場所なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

##--------------------------------------------------------------------------------------------------------------------------------------
#阿部スペース
    #「会津」に対しての返信 「求める景色」について質問する
    elif content in ['会津']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.雪景色',
                        data='callback',
                        text='会津.雪景色'   
                    ),
                    PostbackTemplateAction(
                        label='会津.紅葉',
                        data='callback',
                        text='会津.紅葉'   
                    ),
                    PostbackTemplateAction(
                        label='会津.夜空',
                        data='callback',
                        text='会津.夜空'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.川 or 海',
                        data='callback',
                        text='会津.川 or 海'   
                    ),
                     PostbackTemplateAction(
                        label='会津.森',
                        data='callback',
                        text='会津.森'   
                    ),
                     PostbackTemplateAction(
                        label='会津.希望なし',
                        data='callback',
                        text='会津.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    
     #「会津.雪景色」に対しての返信 「求める効能」について質問する
    elif content in ['会津.雪景色']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.雪景色.美肌',
                        data='callback',
                        text='会津.雪景色.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='会津.雪景色.傷',
                        data='callback',
                        text='会津.雪景色.傷'   
                    ),
                    PostbackTemplateAction(
                        label='会津.雪景色.貧血',
                        data='callback',
                        text='会津.雪景色.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.雪景色.生活習慣病',
                        data='callback',
                        text='会津.雪景色.生活習慣病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.雪景色.皮膚病',
                        data='callback',
                        text='会津.雪景色.皮膚病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.雪景色.希望なし',
                        data='callback',
                        text='会津.雪景色.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        
    
     #「会津.紅葉」に対しての返信 「求める効能」について質問する
    elif content in ['会津.紅葉']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.紅葉.美肌',
                        data='callback',
                        text='会津.紅葉.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='会津.紅葉.傷',
                        data='callback',
                        text='会津.紅葉.傷'   
                    ),
                    PostbackTemplateAction(
                        label='会津.紅葉.貧血',
                        data='callback',
                        text='会津.紅葉.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.紅葉.生活習慣病',
                        data='callback',
                        text='会津.紅葉.生活習慣病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.紅葉.皮膚病',
                        data='callback',
                        text='会津.紅葉.皮膚病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.紅葉.希望なし',
                        data='callback',
                        text='会津.紅葉.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        
        
    #「会津.夜空」に対しての返信 「求める効能」について質問する
    elif content in ['会津.夜空']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.夜空.美肌',
                        data='callback',
                        text='会津.夜空.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='会津.夜空.傷',
                        data='callback',
                        text='会津.夜空.傷'   
                    ),
                    PostbackTemplateAction(
                        label='会津.夜空.貧血',
                        data='callback',
                        text='会津.夜空.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.夜空.生活習慣病',
                        data='callback',
                        text='会津.夜空.生活習慣病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.夜空.皮膚病',
                        data='callback',
                        text='会津.夜空.皮膚病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.夜空.希望なし',
                        data='callback',
                        text='会津.夜空.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        
     #「会津.川 or 海」に対しての返信 「求める効能」について質問する
    elif content in ['会津.川 or 海']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.川 or 海.美肌',
                        data='callback',
                        text='会津.川 or 海.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='会津.川 or 海.傷',
                        data='callback',
                        text='会津.川 or 海.傷'   
                    ),
                    PostbackTemplateAction(
                        label='会津.川 or 海.貧血',
                        data='callback',
                        text='会津.川 or 海.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.川 or 海.生活習慣病',
                        data='callback',
                        text='会津.川 or 海.生活習慣病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.川 or 海.皮膚病',
                        data='callback',
                        text='会津.川 or 海.皮膚病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.川 or 海.希望なし',
                        data='callback',
                        text='会津.川 or 海.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        
    #「会津.森」に対しての返信 「求める効能」について質問する
    elif content in ['会津.森']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.森.美肌',
                        data='callback',
                        text='会津.森.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='会津.森.傷',
                        data='callback',
                        text='会津.森.傷'   
                    ),
                    PostbackTemplateAction(
                        label='会津.森.貧血',
                        data='callback',
                        text='会津.森.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.森.生活習慣病',
                        data='callback',
                        text='会津.森.生活習慣病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.森.皮膚病',
                        data='callback',
                        text='会津.森.皮膚病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.森.希望なし',
                        data='callback',
                        text='会津.森.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        
    #「会津.景色なし」に対しての返信 「求める効能」について質問する
    elif content in ['会津.景色なし']:
        
        carousel_columns = [
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='会津.景色なし.美肌',
                        data='callback',
                        text='会津.景色なし.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='会津.景色なし.傷',
                        data='callback',
                        text='会津.景色なし.傷'   
                    ),
                    PostbackTemplateAction(
                        label='会津.景色なし.貧血',
                        data='callback',
                        text='会津.景色なし.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望す効能を選択してください',
                title='効能で検索',
                actions=[
                     PostbackTemplateAction(
                        label='会津.景色なし.生活習慣病',
                        data='callback',
                        text='会津.景色なし.生活習慣病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.景色なし.皮膚病',
                        data='callback',
                        text='会津.景色なし.皮膚病'   
                    ),
                     PostbackTemplateAction(
                        label='会津.景色なし.希望なし',
                        data='callback',
                        text='会津.景色なし.希望なし'   
                    )
                    
                ]
            )
            
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        


   
#------------------------------------------------------------------------------------------------------------------------------------------------
##佐久間スペース
##「浜通り」と受け取った時の処理
    elif content in ['浜通り']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='景色で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.雪景色',
                        data='callback',
                        text='浜通り.雪景色'   
                    ),
                    PostbackTemplateAction(
                        label='浜通り.紅葉',
                        data='callback',
                        text='浜通り.紅葉'   
                    ),
                    PostbackTemplateAction(
                        label='浜通り.夜空',
                        data='callback',
                        text='浜通り.夜空'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='景色で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.川 or 海',
                        data='callback',
                        text='浜通り.川 or 海'
                    ),
                
                    
                    PostbackTemplateAction(
                        label='浜通り.森',
                        data='callback',
                        text='浜通り.森'
                    ),
                    
        
                    PostbackTemplateAction(
                        label='浜通り.景色なし',
                        data='callback',
                        text='浜通り.景色なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    ##「浜通り.雪景色」と受け取った時の処理
    elif content in ['浜通り.雪景色']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.雪景色.美肌',
                        data='callback',
                        text='浜通り.雪景色.美肌'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.雪景色.傷',
                        data='callback',
                        text='浜通り.雪景色.傷'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.雪景色.貧血',
                        data='callback',
                        text='浜通り.雪景色.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.雪景色.生活習慣病',
                        data='callback',
                        text='浜通り.雪景色.生活習慣病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.雪景色.皮膚病',
                        data='callback',
                        text='浜通り.雪景色.皮膚病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.雪景色.効能なし',
                        data='callback',
                        text='浜通り.雪景色.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    ##「浜通り.紅葉」と受け取った時の処理
    elif content in ['浜通り.紅葉']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.紅葉.美肌',
                        data='callback',
                        text='浜通り.紅葉.美肌'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.紅葉.傷',
                        data='callback',
                        text='浜通り.紅葉.傷'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.紅葉.貧血',
                        data='callback',
                        text='浜通り.紅葉.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.紅葉.生活習慣病',
                        data='callback',
                        text='浜通り.紅葉.生活習慣病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.紅葉.皮膚病',
                        data='callback',
                        text='浜通り.紅葉.皮膚病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.紅葉.効能なし',
                        data='callback',
                        text='浜通り.紅葉.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    ##「浜通り.夜空」と受け取った時の処理
    elif content in ['浜通り.夜空']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.夜空.美肌',
                        data='callback',
                        text='浜通り.夜空.美肌'   
                    ),
                
                    PostbackTemplateAction(
                        label='浜通り.夜空.傷',
                        data='callback',
                        text='浜通り.夜空.傷'   
                    ),
                
            
                    PostbackTemplateAction(
                        label='浜通り.夜空.貧血',
                        data='callback',
                        text='浜通り.夜空.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.夜空.生活習慣病',
                        data='callback',
                        text='浜通り.夜空.生活習慣病'
                    ),

                    PostbackTemplateAction(
                        label='浜通り.夜空.皮膚病',
                        data='callback',
                        text='浜通り.夜空.皮膚病'
                    ),
                    
                    PostbackTemplateAction(
                        label='浜通り.夜空.効能なし',
                        data='callback',
                        text='浜通り.夜空.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    ##「浜通り.川 or 海」と受け取った時の処理
    elif content in ['浜通り.川 or 海']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.川 or 海.美肌',
                        data='callback',
                        text='浜通り.川 or 海.美肌'   
                    ),
                    
                    PostbackTemplateAction(
                        label='浜通り.川 or 海.傷',
                        data='callback',
                        text='浜通り.川 or 海.傷'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.川 or 海.貧血',
                        data='callback',
                        text='浜通り.川 or 海.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.川 or 海.生活習慣病',
                        data='callback',
                        text='浜通り.川 or 海.生活習慣病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.川 or 海.皮膚病',
                        data='callback',
                        text='浜通り.川 or 海.皮膚病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.川 or 海.効能なし',
                        data='callback',
                        text='浜通り.川 or 海.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    ##「浜通り.森」と受け取った時の処理
    elif content in ['浜通り.森']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.森.美肌',
                        data='callback',
                        text='浜通り.森.美肌'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.森.傷',
                        data='callback',
                        text='浜通り.森.傷'   
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.森.貧血',
                        data='callback',
                        text='浜通り.森.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.森.生活習慣病',
                        data='callback',
                        text='浜通り.森.生活習慣病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.森.皮膚病',
                        data='callback',
                        text='浜通り.森.皮膚病'
                    ),
                
                
                    PostbackTemplateAction(
                        label='浜通り.森.効能なし',
                        data='callback',
                        text='浜通り.森.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
##「浜通り.景色なし」と受け取った時の処理
    elif content in ['浜通り.景色なし']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.景色なし.美肌',
                        data='callback',
                        text='浜通り.景色なし.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='浜通り.景色なし.傷',
                        data='callback',
                        text='浜通り.景色なし.傷'   
                    ),
                    PostbackTemplateAction(
                        label='浜通り.景色なし.貧血',
                        data='callback',
                        text='浜通り.景色なし.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='浜通り.景色なし.生活習慣病',
                        data='callback',
                        text='浜通り.景色なし.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='浜通り.景色なし.皮膚病',
                        data='callback',
                        text='浜通り.景色なし.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='浜通り.景色なし.効能なし',
                        data='callback',
                        text='浜通り.景色なし.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )





#------------------------------------------------------------------------------------------------------------------------------------------------
##水戸スペース
##中通りと受け取った時の処理
    elif content in ['中通り']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='景色で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.雪景色',
                        data='callback',
                        text='中通り.雪景色'   
                    ),
                
                    PostbackTemplateAction(
                        label='中通り.紅葉',
                        data='callback',
                        text='中通り.紅葉'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.夜空',
                        data='callback',
                        text='中通り.夜空'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='景色で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.川 or海',
                        data='callback',
                        text='中通り.川 or 海'
                    ),
                    PostbackTemplateAction(
                        label='中通り.森',
                        data='callback',
                        text='中通り.森'
                    ),
                    PostbackTemplateAction(
                        label='中通り.景色なし',
                        data='callback',
                        text='中通り.景色なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
    )
##中通り.雪景色を受け取った時の処理
    elif content in ['中通り.雪景色']:
        carousel_columns = [
            CarouselColumn(
                text='希望する泉質名を選択してください',
                title='泉質名で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.雪景色.美肌',
                        data='callback',
                        text='中通り.雪景色。美肌'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.雪景色.傷',
                        data='callback',
                        text='中通り.雪景色.傷'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.雪景色.貧血',
                        data='callback',
                        text='中通り.雪景色.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='景色で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.雪景色.生活習慣病',
                        data='callback',
                        text='中通り.雪景色.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.雪景色.皮膚病',
                        data='callback',
                        text='中通り.雪景色.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.雪景色.効能なし',
                        data='callback',
                        text='中通り.雪景色.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        ##「中通り.紅葉」と受け取った時の処理
    elif content in ['中通り.紅葉']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.紅葉.美肌',
                        data='callback',
                        text='中通り.紅葉.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.紅葉.傷',
                        data='callback',
                        text='中通り.紅葉.傷'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.紅葉.貧血',
                        data='callback',
                        text='中通り.紅葉.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.紅葉.生活習慣病',
                        data='callback',
                        text='中通り.紅葉.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.紅葉.皮膚病',
                        data='callback',
                        text='中通り.紅葉.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.紅葉.効能なし',
                        data='callback',
                        text='中通り.紅葉.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
    )
    ##「中通り.夜空」と受け取った時の処理
    elif content in ['中通り.夜空']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.夜空.美肌',
                        data='callback',
                        text='中通り.夜空.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.夜空.傷',
                        data='callback',
                        text='中通り.夜空.傷'   
                    ),      
                    PostbackTemplateAction(
                        label='中通り.夜空.貧血',
                        data='callback',
                        text='中通り.夜空.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.夜空.生活習慣病',
                        data='callback',
                        text='中通り.夜空.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.夜空.皮膚病',
                        data='callback',
                        text='中通り.夜空.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.夜空.効能なし',
                        data='callback',
                        text='中通り.夜空.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        ##「中通り.川 or 海」と受け取った時の処理
    elif content in ['中通り.川 or 海']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.川 or 海.美肌',
                        data='callback',
                        text='中通り.川 or 海.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.川 or 海.傷',
                        data='callback',
                        text='中通り.川 or 海.傷'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.川 or 海.貧血',
                        data='callback',
                        text='中通り.川 or 海.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.川 or 海.生活習慣病',
                        data='callback',
                        text='中通り.川 or 海.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.川 or 海.皮膚病',
                        data='callback',
                        text='中通り.川 or 海.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.川 or 海.効能スキップ',
                        data='callback',
                        text='中通り.川 or 海.効能スキップ'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        ##「中通り.森」と受け取った時の処理
    elif content in ['中通り.森']:
        carousel_columns = [
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.森.美肌',
                        data='callback',
                        text='中通り.森.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.森.傷',
                        data='callback',
                        text='中通り.森.傷'   
                    ),
                    PostbackTemplateAction(
                        label='中通り.森.貧血',
                        data='callback',
                        text='中通り.森.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する効能を選択してください',
                title='効能で検索',
                actions=[
                    PostbackTemplateAction(
                        label='中通り.森.生活習慣病',
                        data='callback',
                        text='中通り.森.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.森.皮膚病',
                        data='callback',
                        text='中通り.森.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='中通り.森.効能なし',
                        data='callback',
                        text='中通り.森.効能なし'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,  
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )


#------------------------------------------------------------------------------------------------------------------------------------------------
##ヤナイスペース
#「場所無し」分岐
#「場所無し」と受け取った場合の処理
    elif content in ['場所無し']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.雪景色',
                        data='callback',
                        text='場所無し.雪景色'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.紅葉',
                        data='callback',
                        text='場所無し.紅葉'   
                    ),
                
                    PostbackTemplateAction(
                        label='場所無し.夜空',
                        data='callback',
                        text='場所無し.夜空'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.川 or 海',
                        data='callback',
                        text='場所無し.川 or 海'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.森',
                        data='callback',
                        text='場所無し.森'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.景色',
                        data='callback',
                        text='場所無し.スキップ'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
#「場所無し.雪景色」と受け取った場合の処理
    elif content in ['場所無し.雪景色']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.雪景色.美肌',
                        data='callback',
                        text='場所無し.雪景色.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.雪景色.傷',
                        data='callback',
                        text='場所無し.雪景色.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.雪景色.貧血',
                        data='callback',
                        text='場所無し.雪景色.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.雪景色.生活習慣病',
                        data='callback',
                        text='場所無し.雪景色.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.雪景色.皮膚病',
                        data='callback',
                        text='場所無し.雪景色.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.雪景色.スキップ',
                        data='callback',
                        text='場所無し.雪景色.スキップ'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

    #「場所無し.紅葉」と受け取った場合の処理
    elif content in ['場所無し.紅葉']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.紅葉.美肌',
                        data='callback',
                        text='場所無し.紅葉.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.紅葉.傷',
                        data='callback',
                        text='場所無し.紅葉.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.紅葉.貧血',
                        data='callback',
                        text='場所無し.紅葉.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.川 or 海.生活習慣病',
                        data='callback',
                        text='場所無し.川 or 海.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.森.皮膚病',
                        data='callback',
                        text='場所無し.森.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.景色なし.効能なし',
                        data='callback',
                        text='場所無し.景色なし.効能なし'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

    #「場所無し.夜空」と受け取った場合の処理
    elif content in ['場所無し.夜空']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.夜空.美肌',
                        data='callback',
                        text='場所無し.夜空.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.夜空.傷',
                        data='callback',
                        text='場所無し.夜空.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.夜空.貧血',
                        data='callback',
                        text='場所無し.夜空.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.夜空.生活習慣病',
                        data='callback',
                        text='場所無し.夜空.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.夜空.皮膚病',
                        data='callback',
                        text='場所無し.夜空.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.夜空.効能なし',
                        data='callback',
                        text='場所無し.夜空.効能なし'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

    #「場所無し.川 or 海」と受け取った場合の処理
    elif content in ['場所無し.川 or 海']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.川 or 海.美肌',
                        data='callback',
                        text='場所無し.川 or 海.美肌'   
                    ),

                    PostbackTemplateAction(
                        label='場所無し.川 or 海.傷',
                        data='callback',
                        text='場所無し.川 or 海.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.川 or 海.貧血',
                        data='callback',
                        text='場所無し.川 or 海.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.川 or 海.生活習慣病',
                        data='callback',
                        text='場所無し.川 or 海.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.川 or 海.皮膚病',
                        data='callback',
                        text='場所無し.川 or 海.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.川 or 海.効能なし',
                        data='callback',
                        text='場所無し.川 or 海.効能なし'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
    
    #「場所無し.森」と受け取った場合の処理
    elif content in ['場所無し.森']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.森.美肌',
                        data='callback',
                        text='場所無し.森.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.森.傷',
                        data='callback',
                        text='場所無し.森.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.森.貧血',
                        data='callback',
                        text='場所無し.森.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.森.生活習慣病',
                        data='callback',
                        text='場所無し.森.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.森.皮膚病',
                        data='callback',
                        text='場所無し.森.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.森.効能なし',
                        data='callback',
                        text='場所無し.森.効能なし'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

     #「場所無し.景色なし」と受け取った場合の処理
    elif content in ['場所なし.景色なし']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.景色なし.美肌',
                        data='callback',
                        text='場所無し.景色なし.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.景色なし.傷',
                        data='callback',
                        text='場所無し.景色なし.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所無し.景色なし.貧血',
                        data='callback',
                        text='場所無し.景色なし.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所無し.景色なし.生活習慣病',
                        data='callback',
                        text='場所無し.景色なし.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.景色なし.皮膚病',
                        data='callback',
                        text='場所無し.景色なし.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所無し.景色なし.効能なし',
                        data='callback',
                        text='場所無し.景色なし.効能なし'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )


     #「場所なし」と受け取った場合の処理
    elif content in ['場所なし.景色なし.美肌']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所なし.景色なし.美肌',
                        data='callback',
                        text='場所なし.景色なし.美肌'   
                    ),
                    PostbackTemplateAction(
                        label='場所なし.景色なし.傷',
                        data='callback',
                        text='場所なし.景色なし.傷'   
                    ),
                    PostbackTemplateAction(
                        label='場所なし.景色なし.貧血',
                        data='callback',
                        text='場所なし.景色なし.貧血'   
                    )
                ]
            ),
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='場所なし.景色なし.生活習慣病',
                        data='callback',
                        text='場所なし.景色なし.生活習慣病'
                    ),
                    PostbackTemplateAction(
                        label='場所なし.景色なし.皮膚病',
                        data='callback',
                        text='場所なし.景色なし.皮膚病'
                    ),
                    PostbackTemplateAction(
                        label='場所なし.景色なし.効能なし',
                        data='callback',
                        text='場所なし.景色なし.効能なし'
                    )
                ]
            )     
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

     #「場所無し.雪景色.美肌」と受け取った場合の処理
    elif content in ['場所なし.雪景色.美肌']:
        carousel_columns = [
            CarouselColumn(
                text='希望する景色を選択してください',
                title='タップで検索',
                actions=[
                    PostbackTemplateAction(
                        label='温泉',
                        data='callback',
                        text='温泉'   
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )


##　　　ここから下は触らない
#-----------------------------------------------------------------------------------------------------------------------------------------------

    # 以下サブカテゴリ
    elif content in ['会津']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 21 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['中通り']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 22 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)
        
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['浜通り']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 23 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['肩こり解消']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 24 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )
    
    elif content in ['肌に良い']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 25 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['雪景色']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 26 ORDER BY Id ASC")
                db = curs.fetchall()
        
        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['紅葉']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 31 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['熱い']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 32 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['ぬるい']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 33 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['高い']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 34 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['安い']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 41 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )












##----------------------------------------------------------------------















    elif content in ['生活・人間関係']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 42 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['食品・安全']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 43 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['その他']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 44 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['環境問題']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 51 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['公害・廃棄物']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 52 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['環境保全活動']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 53 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['労働環境']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 71 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['経営']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 72 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['農林水産業']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 731 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['テクノロジー']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 732 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['安全相談']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 81 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['交通安全']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 82 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['いじめ・子ども相談']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 83 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['犯罪関連']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 84 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['パスポート']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 91 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['外国人向け相談窓口']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 101 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['教育相談']:

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 111 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )











##------------------------------------------------------------------
    














    
    # 以下 下位分類のあるサブカテゴリ
    elif content in ['産業']:
        carousel_columns = [
            CarouselColumn(
                text = '分野を選択してください',
                title = '分野選択',
                actions = [
                    PostbackTemplateAction(
                        label = '農林水産業',
                        data = 'callback',
                        text = '農林水産業'
                    ),
                    PostbackTemplateAction(
                        label = 'テクノロジー',
                        data = 'callback',
                        text = 'テクノロジー'
                    ),
                    
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

    elif content in ['障がい児関連']:

        carousel_columns = [
            CarouselColumn(
                text = '分野を選択してください',
                title = '分野選択',
                actions = [
                    PostbackTemplateAction(
                        label = '視覚障がい',
                        data = 'callback',
                        text = '視覚障がい'
                    ),
                    PostbackTemplateAction(
                        label = '聴覚障がい',
                        data = 'callback',
                        text = '聴覚障がい'
                    ),
                    PostbackTemplateAction(
                        label = '肢体不自由',
                        data = 'callback',
                        text = '肢体不自由'
                    )
                ]
            ),
            CarouselColumn(
                text = '分野を選択してください',
                title = '分野選択',
                actions = [
                    PostbackTemplateAction(
                        label = '病弱障がい',
                        data = 'callback',
                        text = '病弱障がい'
                    ),
                    PostbackTemplateAction(
                        label = '知的障がい',
                        data = 'callback',
                        text = '知的障がい'
                    ),
                    PostbackTemplateAction(
                        label = 'LD・ADHD等',
                        data = 'callback',
                        text = 'LD・ADHD等'
                    )
                ]
            )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )

    # 以下 下位分類
    elif content in ['視覚障がい']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 1121 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['聴覚障がい']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 1122 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['肢体不自由']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 1123 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['病弱障がい']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 1124 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['知的障がい']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 1125 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['LD・ADHD等']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 1126 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    elif content in ['調査・文化財']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE subcategory = 113 ORDER BY Id ASC")
                db = curs.fetchall()

        result = window_list_flex(db)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='flex template', contents=result)
        )

    # 県政相談
    elif content in ['県政相談']:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE Id = 1")
                db = curs.fetchall()

        result = "お探しの窓口はこちらですか？\n\n" + window_info(db)
        
        review = "よかったら、今回の会話が役に立ったか教えてください！"

        review_qa = ButtonsTemplate(
            text = '今回の会話は',
            actions = [
                PostbackTemplateAction(
                    label = '役に立った',
                    data = 'callback',
                    text = '役に立った'
                ),
                PostbackTemplateAction(
                    label = '役に立たなかった',
                    data = 'callback',
                    text = '役に立たなかった'
                )
            ]
        )

        messages = [
            TextSendMessage(text=result),
            TextSendMessage(text=review),
            TemplateSendMessage(alt_text='carousel template', template=review_qa)
            ]
        line_bot_api.reply_message(event.reply_token, messages)
    
    # 指定の窓口の情報を表示
    elif content[:5] in ['窓口ID:']:
        window_id = content[5:]

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM window_list WHERE Id = " + str(window_id))
                db = curs.fetchall()

        # 「窓口ID:999」など、存在しない窓口IDを入力された場合の処理
        if len(db) == 0:
            response = "存在しない窓口IDが入力されました。\n" +\
            "もう一度利用する場合はボタンを押してください。"

            button = ButtonsTemplate(
                text = 'もう一度利用する',
                actions = [
                    PostbackTemplateAction(
                        label = 'カテゴリ選択へ',
                        data = 'callback',
                        text = 'カテゴリ選択'
                    )
                ]
            )

            messages = [
                TextSendMessage(text=response),
                TemplateSendMessage(alt_text='carousel template', template=button)
                ]
            line_bot_api.reply_message(event.reply_token, messages)


        # 見つからなかった場合の処理
        if window_id in ['1']:
            result = "見つからなかった場合はこちらからご相談ください。\n\n"
        else:
            result = "お探しの窓口はこちらですか？\n\n"

        result += window_info(db)

        review = "よかったら、今回の会話が役に立ったか教えてください！"

        review_qa = ButtonsTemplate(
            text = '今回の会話は',
            actions = [
                PostbackTemplateAction(
                    label = '役に立った',
                    data = 'callback',
                    text = '役に立った'
                ),
                PostbackTemplateAction(
                    label = '役に立たなかった',
                    data = 'callback',
                    text = '役に立たなかった'
                )
            ]
        )

        messages = [
            TextSendMessage(text=result),
            TextSendMessage(text=review),
            TemplateSendMessage(alt_text='carousel template', template=review_qa)
            ]
        line_bot_api.reply_message(event.reply_token, messages)

    # 「最初から」がタップされた場合の処理
    elif content in ['最初から']:
        response = "改めて窓口を探す際には、もう一度「カテゴリ選択」をタップしてください。"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)) 
    
    # 「役に立った」「役に立たなかった」へのレスポンス
    elif content in ['役に立った', '役に立たなかった']:
        response = "回答ありがとうございました！\n" +\
            "もう一度利用する場合はボタンを押してください。"

        button = ButtonsTemplate(
            text = 'もう一度利用する',
            actions = [
                PostbackTemplateAction(
                    label = 'カテゴリ選択へ',
                    data = 'callback',
                    text = 'カテゴリ選択'
                )
            ]
        )

        messages = [
            TextSendMessage(text=response),
            TemplateSendMessage(alt_text='carousel template', template=button)
            ]
        line_bot_api.reply_message(event.reply_token, messages)

    # その他              
    else:
        response = "ごめんなさい。メッセージを処理できませんでした。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)) 

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
