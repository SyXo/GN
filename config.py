"""Configuration file for GNBot"""
import pymysql.cursors

TOKEN = '1077848786:AAHfMrRKadc3Plo14rpE7dPJJC3bVbbVod0'  # Release bot TOKEN
TEST_TOKEN = '839168325:AAGtBUzQoqdPSSHPWUeo4K9Onxxnclv96sA'  # Test bot TOKEN

# API's
API = {'API_Weather': 'http://' + 'api.openweathermap.org/data/2.5/weather?q={}&appid=579cbfee514bcc3d3bec44b7ef405340'
                                  '&units=metric&leng=ru',
       'API_Gif': 'https://' + 'api.giphy.com/v1/gifs/random?api_key=mHVzi8lTLfPjh2qIAoXcN8P8QLeVRlvh&' \
                               'tag=weapons, cars, girls, funny, cats, sex, drugs, programming, anime, hentai' \
                               'guns, gaming, science, memes'
                               '&rating=R',
       'API_Meme': 'https://' + 'meme-api.herokuapp.com/gimme',
       'API_Deezer': 'https://' + 'api.deezer.com/search/'
       }

URLS = {'memes': ['https://' + 'www.reddit.com/r/Pikabu/search?q=flair%3AМем&restrict_sr=1&sort=new']}  # Memes URL

BD_CONNECT = {'user': 'UltraXionUA',  # Python Anywhere DB
              'password': 'DB25813123321',
              'host': 'UltraXionUA.mysql.pythonanywhere-services.com',
              'database': 'UltraXionUA$test',
              'cursorclass': pymysql.cursors.DictCursor
              }

# BD_CONNECT = {'unix_socket': '/Applications/MAMP/tmp/mysql/mysql.sock',  # Local DB
#               'user': 'root',
#               'password': 'root',
#               'db': 'Bot_DB',
#               'charset': 'utf8mb4',
#               'cursorclass': pymysql.cursors.DictCursor
#               }

# api.telegram.org/bot1077848786:AAHfMrRKadc3Plo14rpE7dPJJC3bVbbVod0/sendMessage  # To add autoposting
# {"chat_id":"-1001339129150","text":" {{Url}}"}
