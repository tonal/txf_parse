# -*- coding: utf-8 -*-
import io

from objects import txf_object_t, txf_file_t

def parseTXF(fname, encoding='cp1251'):
  u"""
  Разбор TXF файла в объекты
  @param fname: имя файла
  @param encoding: кодировка
  @return: Объект txf_file_t
  """
  # Импортируем имена из модуля pyparsing - построитель разборщиков
  from pyparsing import Word, Suppress, White, Group, OneOrMore, ZeroOrMore
  from pyparsing import nums, alphas, restOfLine, oneOf

  # Описание грамматики TXF файла

  # Общие определения
  number = Word(nums)               # целое число
  dot_number = Word(nums + u'.-')   # число с точкой
  skip_endl = Suppress(restOfLine)  # Отбрасываемый конец строки
  skip_space = Suppress(White())    # Отбрасываемые пробелы/табуляции

  # Строки объекта
  obj_hdr = Group(u'.OBJ' + number + Word(alphas)) + skip_endl  # Заголовок
  obj_key = Group(u'.KEY' + number) + skip_endl                 # Собственный номер
  obj_fld = Group(Word(u'.', alphas) + skip_space + restOfLine) # Характеристика
  coord = Group(dot_number + dot_number) + skip_endl            # Строка координат

  # Координаты объекта
  # начинаются со строки с количеством, за которой идут строки с координатами
  obj_coords = number + skip_endl + OneOrMore(coord)

  def parseCoord(s, loc, tocs):
    u'Преобразование списка токенов в список координат'
    n = int(tocs[0])
    coords = tuple((x, y) for [x, y] in tocs[1:])
    if n != len(coords):
      # Ошибка, если заявленное количество не соврадает с реальным
      raise ParseFatalException(
        s, loc, u'need %d coord, but present %d' % (n, len(coords)))
    return [coords]
  obj_coords.setParseAction(parseCoord)

  # Строки семантика объекта
  obj_sem_hdr = Group(u'.SEM' + number) + skip_endl       # Заголовок с количеством
  obj_sem_line = Group(number + skip_space + restOfLine)  # Строка семантики
  # Семантика объекта
  # Начинается с заголовка, за которым идут строки семантики
  obj_sem = obj_sem_hdr + OneOrMore(obj_sem_line)

  def parseSem(s, loc, tocs):
    u"Преобразование списка токенов в хеш семантики"
    n = int(tocs[0][1]) # '.SEM' + number
    sem_dict = dict((num, val.rstrip()) for [num, val] in tocs[1:])
    if n != len(sem_dict):
      # Ошибка, если заявленное количество не соврадает с реальным
      raise ParseFatalException(
        s, loc, u'need %d sems, but present %d' % (n, len(sem_dict)))
    return [sem_dict]
  obj_sem.setParseAction(parseSem)

  # Объект TXF
  # Начинается с заголовка, за которым идут собственный номер и/или
  # характеристики, после чего координаты и семантика
  obj = obj_hdr + OneOrMore(obj_key | obj_fld) + obj_coords + obj_sem

  def parseObjStart(tocs):
    u"Преобразование списка токенов в общие поля объекта TXF"
    cls_code, loc_code = tocs[0][1:]
    flds = dict((name, val.rstrip()) for name, val in tocs[1:-2])
    key = int(flds['.KEY'])
    coords = tocs[-2]
    return (cls_code, loc_code, flds, key, coords)

  def parseObj(tocs):
    u"Преобразование списка токенов в объект TXF"
    cls_code, loc_code, flds, key, coords = parseObjStart(tocs)
    sems = tocs[-1]
    return [
      txf_object_t(cls_code, loc_code, key, flds, coords, sems=sems)]
  obj.setParseAction(parseObj)

  # Строки объекта подписи
  obj_tit_hdr = Group(u'.OBJ' + number + u'TIT') + skip_endl  # Заголовок
  obj_tit_str = Group(u'>' + restOfLine)                      # Текст подписи

  # Объект подписи
  # Вместо семантики содержит текст подписи
  obj_tit = (
    obj_tit_hdr + OneOrMore(obj_key | obj_fld) + obj_coords + obj_tit_str
  )
  def parseObjTit(tocs):
    u"Преобразование списка токенов в объект подписи TXF"
    cls_code, loc_code, flds, key, coords = parseObjStart(tocs)
    title = tocs[-1][1].rstrip()
    return [
      txf_object_t(cls_code, loc_code, key, flds, coords, title=title)]
  obj_tit.setParseAction(parseObjTit)

  # Строки файла
  header = Group(oneOf(u'.SXF .SIT') + dot_number) + skip_endl  # Заголовок с версией
  passport = Group(Word(u'P', nums) + skip_space + restOfLine)  # Строка паспорта
  objs_start = Group(u'.DAT' + number) + skip_endl              # Начало объектов
  end_file = u'.END' + skip_endl                                # Конец файла

  # Файл состоит из
  # Заголовка, паспортных данных, строки начала объектов, самих объектов
  # и строки конца
  txf = (
    header + Group(ZeroOrMore(passport))
    + objs_start + OneOrMore(obj_tit | obj) + end_file)

  def parseObjs(s, loc, tocs):
    u"Преобразование списка токенов в объект файла TXF"
    magic = tocs[0][0]
    version = tocs[0][1]
    passports = dict((pkey, pval.rstrip()) for pkey, pval in tocs[1])
    n = int(tocs[2][1])
    objs = tocs[3:-1]
    if n != len(objs):
      # Ошибка, если заявленное количество не соврадает с реальным
      raise ParseFatalException(
        s, loc, u'need %d objs, but present %d' % (n, len(objs)))
    return [txf_file_t(magic, version, passports, objs[:])]
  txf.setParseAction(parseObjs)

  # Открываем файл, разбираем и возвращаем результат
  parsed = txf.parseFile(io.open(fname, encoding=encoding))
  return parsed[0]
