from Server.server import app

version = '0.1.0'

if __name__ == '__main__' :
    
    print('-------------------------------')
    print('Yokai - version ' + version)
    print('-------------------------------')
    
    print('\r\nHello User.\r\n')
    
    app.run(host='0.0.0.0', port=5001)