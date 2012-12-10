# -*- coding: utf-8 -*-
from parse import parseTXF

class txf_object_t(object):
  u"Объект из TXF файла"
  cls_code = 0    # Классификационный код
  loc_code = u''  # Характер локализации
  key = 0         # Собственный номер объекта
  flds = {}       # Характеристики (включая собственный номер)
  coords = ()     # Координаты
  title = u''     # Текст подписи
  sems = {}       # Семантика

  def __init__(
    self, cls_code, loc_code, key=None, flds={}, coords=(), title=u'', sems={}
  ):
    super(txf_object_t, self).__init__()
    self.cls_code = cls_code
    self.loc_code = loc_code
    if key is None:
      key = flds['.KEY']
    elif '.KEY' not in flds:
      flds['.KEY'] = key
    self.key = key
    self.flds = flds
    self.coords = coords
    self.title = title
    self.sems = sems

class txf_file_t(object):
  u"Представление TXF файла"
  magic = u''     # Заголовок .SXF | .SIT
  version = u''   # Версия
  passport = {}   # Данные паспорта
  objs = ()       # Кортеж объектов

  def __init__(self, magic, version, passport={}, objs=()):
    super(txf_file_t, self).__init__()
    self.magic = magic
    self.version = version
    self.passport = passport
    self.objs = objs

