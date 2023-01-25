from pprint import pprint
import serial
import crcmod
import re
import time
import pandas as pd, numpy as np

def stop():
    while True:
        pass

# String 2 Bytes:
# bytes = string.encode('utf-8')
# Bytes 2 String
# string = bytes.encode('utf-8')

class BytesForPySerial(str):
    def str2hexbytes(self):
        self = bytes.fromhex(self)
        return self

class BytesFromPySerial(bytes):
    def bytes2hexstr(self):
        self = self.hex()
        return self

def symbol_replacer(is_TX, str_in):
    '''
    :param is_TX: bool type, True - do replace, False - reverse replace
    :param str_in: str type
    '''
    if is_TX:
        str_in = str_in.replace('7d', '7d5d')
        str_in = str_in.replace('7f', '7d5f')
        str_in = str_in.replace('7e', '7d5e')
    else:
        str_in = str_in.replace('7d5d', '7d')
        str_in = str_in.replace('7d5f', '7f')
        str_in = str_in.replace('7d5e', '7e')
    return str_in

def search_available_COM_ports():
    '''
    Перебирает порты с COM0 до COM9 и возвращает список портов которые удалось открыть на скорости 512000.
    '''
    list_of_COM = []
    for i in range(10):
        com = 'COM' + str(i)
        try:
            ser = serial.Serial(com, 512000, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE,
                                bytesize=serial.EIGHTBITS, timeout=0.0001)
            list_of_COM.append(com)
            ser.close()
            # print(com, 'доступен!')
        except serial.serialutil.SerialException:
            pass
            # print(com, 'не подключён...')
    return list_of_COM

def set_skew_old(skew):
    '''
    :param skew: str
    '''
    if ser.is_open == False:
        ser.open()
    if len(skew) == 1:
        skew = '0' + skew
    print('Set skew =', skew)
    data = '2200000500608600' + skew + '00'
    CRC8 = calc_crc8(data)
    data += CRC8
    data = symbol_replacer(True, data)

    ser.write(b'\x7E\x55\x55\x55\x55\x55\x55\x55\xD5') #SOP
    ser.write(BytesForPySerial(data).str2hexbytes())
    # ser.write(data.encode('utf-8'))
    # ser.write(CRC8)
    ser.write(b'\x7F') #EOP
    print('Set skew done!')
    return

def reset_errors():
    if ser.is_open == False:
        ser.open()
    data = '33000005000000000000'
    CRC8 = calc_crc8(data)
    data += CRC8
    data = symbol_replacer(True, data)

    ser.write(b'\x7E\x55\x55\x55\x55\x55\x55\x55\xD5') #SOP
    ser.write(BytesForPySerial(data).str2hexbytes())
    ser.write(b'\x7F') #EOP
    print('Reset errors DONE!')
    return

def get_errors():
    if ser.is_open == False:
        ser.open()
    print('Get errors...')
    data = '33000005000100000000'
    CRC8 = calc_crc8(data)
    data += CRC8
    data = symbol_replacer(True, data)

    ser.write(b'\x7E\x55\x55\x55\x55\x55\x55\x55\xD5') #SOP
    ser.write(BytesForPySerial(data).str2hexbytes())
    ser.write(b'\x7F') #EOP

    time.sleep(0.01)
    bytes_loaded = ser.inWaiting()
    rx_line = ser.read(bytes_loaded)
    rx_line = BytesFromPySerial(rx_line).bytes2hexstr()
    rx_line = symbol_replacer(False, rx_line)
    print('\t\tRX:', rx_line)
    if rx_line.startswith('7e') and rx_line.endswith('7f'):
        print('\t\tPackage OK!')
    rx_data = re.findall('^7e(........)(........)(........)7f$', rx_line)
    try:
        errors_val = int(rx_data[0][0], 16)
        good_packages_val = int(rx_data[0][1], 16)
        tx_packages_val = int(rx_data[0][2], 16)
    except IndexError:
        errors_val = -1
        good_packages_val = 0
        tx_packages_val = 0

    print('\t\tКоличество ошибок:', errors_val)
    print('\t\tКоличество успешных передач:', good_packages_val)
    print('\t\tКоличество сгенерированных тестовых посылок:', tx_packages_val)
    print('\t\tGet errors done!')
    return (errors_val, good_packages_val, tx_packages_val)


crc8_func = crcmod.mkCrcFun(0x131, 0x0, 0x0)
def calc_crc8(data_str):
    '''
    Расчёт CRC8 (string) для строковых входных данных.
    Перед вызовом функции должна быть определена функция crc8_func = crcmod.mkCrcFun(0x131, 0x0, 0x0)
    '''
    if len(data_str) % 2:
        data_str = '0' + data_str
    data_str = re.findall(r'\w\w', data_str)
    byte_tuple = tuple()
    for i in range(len(data_str)):
        data_str[i] = bytes(data_str[i], encoding='utf-8')
        data_str[i] = data_str[i].decode('utf-8')
        data_str[i] = int(data_str[i], 16)
        byte_tuple = byte_tuple + (data_str[i],)
    # crc8_func = crcmod.mkCrcFun(0x131, 0x0, 0x0)
    crc8 = hex(crc8_func(bytearray(byte_tuple)))
    crc8_str = ''.join(list(crc8)[2:])
    if len(crc8_str) == 1:
        crc8_str = '0' + crc8_str
    return crc8_str


def imit_control(is_ON):
    '''
    :param is_ON: bool
    '''
    if ser.is_open == False:
        ser.open()
    print('Imitation ', 'ON' if is_ON else 'OFF', '...', sep='', end=' ')
    is_ON = '01' if is_ON else '00'
    data = '330000050002' + is_ON + '000000'
    CRC8 = calc_crc8(data)
    data += CRC8
    # print('TX:', data)
    data = symbol_replacer(True, data)

    ser.write(b'\x7E\x55\x55\x55\x55\x55\x55\x55\xD5') #SOP
    ser.write(BytesForPySerial(data).str2hexbytes())
    ser.write(b'\x7F') #EOP
    print('DONE!')
    return

def set_skew(skew, port):
    '''
    :param skew, port: hex int (0x00)
    '''
    if ser.is_open == False:
        ser.open()
    mdio_operation(True, port, 0x86, skew)
    print('Set skew = ', hex(skew), '... DONE!', sep='')
    return

def mdio_operation(is_wr, port, reg, data):
    '''
    port, reg, data format: 0xXXXX (HEX int)
    is_wr -- bool, True - write, False - read
    '''
    print('MDIO operation...')
    op_port = hex((0x60 if is_wr else 0x40) + port)[2:]
    reg = hex(reg)[2:]
    data = hex(data)[2:]
    while len(reg) < 4:
        reg = '0' + reg
    while len(data) < 4:
        data = '0' + data
    reg = reg[2:] + reg[:2]
    data = data[2:] + data[:2]

    data_tx = '2200000500' + op_port + reg + data
    CRC8 = calc_crc8(data_tx)
    data_tx += CRC8
    print('\t\tmdio TX:', data_tx)
    data_tx = symbol_replacer(True, data_tx)

    ser.write(b'\x7E\x55\x55\x55\x55\x55\x55\x55\xD5')
    ser.write(BytesForPySerial(data_tx).str2hexbytes())
    ser.write(b'\x7F')

    if is_wr:
        return
    else:
        time.sleep(0.01)
        bytes_loaded = ser.inWaiting()
        print('num of bytes:', bytes_loaded)
        rx_line = ser.read(bytes_loaded)
        if ser.inWaiting():
            print('\t\tОстаток данных в буфере:', ser.readline())
        rx_line = BytesFromPySerial(rx_line).bytes2hexstr()
        rx_line = symbol_replacer(False, rx_line)
        print('\t\tmdio RX:', rx_line)
        if rx_line.startswith('7e') and rx_line.endswith('7f'):
            print('\t\tPackage OK!', end=' ')
        rx_data = re.findall('^7e(..........)(..)(..)(..)(..)(..)7f$', rx_line)
        try:
            rd_data = rx_data[0][5] + rx_data[0][4]
            rd_addr = rx_data[0][3] + rx_data[0][2]
            rd_port = rx_data[0][1]
        except IndexError:
            rd_data = -1
            rd_addr = -1
            rd_port = -1
        print('Считанные данные port/addr/data: ', rd_port, '/', rd_addr, '/', rd_data, sep='')
        return (rd_port, rd_addr, rd_data)

def digital_loopback(is_ON, port):
    '''
    :param is_ON: bool, True - enable, False - disable
    :param port: hex int, 0xXX
    '''
    if ser.is_open == False:
        ser.open()
    if is_ON:
        mdio_operation(True, port, 0x001F, 0x8000) # reset
        while mdio_operation(False, port, 0x0000, 0xffff)[2] != '1140':
            print('waiting...')
            time.sleep(0.1)
        mdio_operation(True, port, 0x0000, 0x0140)
        mdio_operation(True, port, 0x0032, 0x00D3)
        mdio_operation(True, port, 0x0016, 0x0004)
        mdio_operation(True, port, 0x001f, 0x4000)
        while mdio_operation(False, port, 0x0000, 0xffff)[2] != '0140':
            print('waiting...')
            time.sleep(0.1)
        print('Digital loopback on Port', port, 'ENABLE!')
    else:
        mdio_operation(True, port, 0x001F, 0x8000) # CHECK!
        print('Digital loopback on Port', port, 'DISABLE!')
    return


# ---->> Старт программы:

print('Доступные COM порты:', *search_available_COM_ports())
com = input('Введите имя одного из доступных COM портов: ')

ser = serial.Serial('COM8', 512000, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE,bytesize=serial.EIGHTBITS,timeout=0.0001)
print(ser.name)
print('Connected to', ser.portstr, end='...\n')
if ser.inWaiting():
    print('Остаток данных в буфере:', ser.readline())


# ---->> Далее идёт моя логика, где я использую объект ser для взаимодействия с COM-портом.
# ------ Наверное в сами функции лучше передавать этот объект, просто тут всё в одном файле
# ------ и одно соединение. И в целом всё на коленке сделано, лишь бы выполнить задачу.

data_list, row_list = [],[]
list_rx, list_tx = [],[]
list_port_df = []

for port in range(0x0, 0x9):
    digital_loopback(True, port=port)
    for skew in range(0x00, 0x100):
        if ser.inWaiting():
            print('Остаток данных в буфере:', ser.readline())
        set_skew(skew=skew, port=port)
        imit_control(True)
        time.sleep(0.2)
        imit_control(False)
        errors_tuple = get_errors()
        # errors_sum = errors_tuple[0] + (errors_tuple[2] - errors_tuple[1])
        errors_sum = errors_tuple[2] - errors_tuple[1]
        skew = hex(skew)[2:]
        if len(skew) == 1:
            skew = '0' + skew
        rx_skew = int(skew[1], 16)
        tx_skew = int(skew[0], 16)
        if rx_skew != 15:
            row_list.append(errors_sum)
        else:
            row_list.append(errors_sum)
            data_list.append(row_list.copy())
            row_list.clear()
    digital_loopback(False, port=port)
    print('append df to of list_df...')
    for i in range(0, 16):
        list_rx.append('RX' + str(i))
        list_tx.append('TX' + str(i))
    port_df = pd.DataFrame(data_list.copy(), index=list_tx, columns=list_rx)
    list_port_df.append(port_df.copy())

    data_list.clear()
    row_list.clear()
    list_rx.clear()
    list_tx.clear()
    print('PORT', port, 'DONE!')

with pd.ExcelWriter('output_table_mux.xlsx', engine='openpyxl') as writer:
    for i in range(len(list_port_df)):
        list_port_df[i].to_excel(writer, sheet_name='port_'+str(i))
stop()

'''
baudrates: 57600, 512000
'''

print('Доступные COM порты:', *search_available_COM_ports())
com = input('Введите имя одного из доступных COM портов: ')
ser = serial.Serial(com, 512000, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE,bytesize=serial.EIGHTBITS,timeout=0.0001)
print(ser.name)
print('Connected to', ser.portstr, end='...\n')
if ser.inWaiting():
    print('Остаток данных в буфере:', ser.readline())

data_list, row_list = [],[]
for skew in range(0x00, 0x100):
    # print('Start test skew =', hex(skew)[2:], ':')
    #skew = hex(skew)[2:] # not required yet
    set_skew(skew)
    reset_errors()
    time.sleep(1)
    error_tuple = get_errors()
    # Save in list:
    errors_sum = error_tuple[0]
    skew = hex(skew)[2:]
    if len(skew) == 1:
        skew = '0' + skew
    rx_skew = int(skew[1], 16)
    tx_skew = int(skew[0], 16)
    if rx_skew != 15:
        row_list.append(errors_sum)
    else:
        row_list.append(errors_sum)
        data_list.append(row_list.copy())
        row_list.clear()
    print()
ser.close()

'''
Generate XLSX-file:
'''
list_rx, list_tx = [], []
for i in range(0, 16):
    list_rx.append('RX' + str(i))
    list_tx.append('TX' + str(i))

my_table_df = pd.DataFrame(data_list, index=list_tx, columns=list_rx)
print(my_table_df)
my_table_df.to_excel('output_table.xlsx')
