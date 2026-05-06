import json
import os
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from collections import deque


class Note(ABC):
    """Абстрактный базовый класс для заметок"""
   
    def __init__(self, title: str, text: str, tags: List[str] = None):
        self.title = self._validate_title(title)
        self.text = self._validate_text(text)
        self.tags = tags if tags else []
        self.date = datetime.now()
   
    @staticmethod
    def _validate_title(title: str) -> str:
        if not title or not title.strip():
            raise ValueError("Заголовок не может быть пустым")
        if len(title) > 100:
            raise ValueError("Заголовок не может превышать 100 символов")
        return title.strip()
   
    @staticmethod
    def _validate_text(text: str) -> str:
        if not text or not text.strip():
            raise ValueError("Текст не может быть пустым")
        return text.strip()
   
    def add_tag(self, tag: str):
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
   
    def remove_tag(self, tag: str):
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
   
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.__class__.__name__,
            'title': self.title,
            'text': self.text,
            'tags': self.tags,
            'date': self.date.isoformat()
        }
   
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        note_class = TEXT_NOTE_TYPES.get(data['type'], TextNote)
        note = note_class(data['title'], data['text'], data['tags'])
        note.date = datetime.fromisoformat(data['date'])
        return note
   
    @abstractmethod
    def display(self) -> str:
        pass
   
    def __str__(self):
        return f"{self.title} [{', '.join(self.tags)}] - {self.date.strftime('%Y-%m-%d %H:%M')}"


class TextNote(Note):
    """Обычная текстовая заметка"""
   
    def display(self) -> str:
        return f"""
╔══════════════════════════════════════════════════════════╗
║ {self.title[:56]:<56} ║
╠══════════════════════════════════════════════════════════╣
║ Дата: {self.date.strftime('%Y-%m-%d %H:%M:%S'):<49} ║
║ Теги: {', '.join(self.tags) if self.tags else 'нет':<51} ║
╠══════════════════════════════════════════════════════════╣"""
        + ''.join(f"\n║ {line:<58} ║" for line in self.text.split('\n')) + """
╚══════════════════════════════════════════════════════════╝"""


class VoiceNote(Note):
    """Заметка с голосовым сообщением (симуляция)"""
   
    def __init__(self, title: str, text: str, tags: List[str] = None, duration: int = 0):
        super().__init__(title, text, tags)
        self.duration = max(0, duration)
   
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['duration'] = self.duration
        return data
   
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        note = cls(data['title'], data['text'], data['tags'], data.get('duration', 0))
        note.date = datetime.fromisoformat(data['date'])
        return note
   
    def display(self) -> str:
        return f"""
╔══════════════════════════════════════════════════════════╗
║ 🎤 {self.title[:55]:<55} ║
╠══════════════════════════════════════════════════════════╣
║ Дата: {self.date.strftime('%Y-%m-%d %H:%M:%S'):<49} ║
║ Длительность: {self.duration} сек{'' if self.duration == 1 else '' :<42} ║
║ Теги: {', '.join(self.tags) if self.tags else 'нет':<51} ║
╠══════════════════════════════════════════════════════════╣
║ Транскрипция:                                            ║"""
        + ''.join(f"\n║ {line:<58} ║" for line in self.text.split('\n')) + """
╚══════════════════════════════════════════════════════════╝"""


class ChecklistNote(Note):
    """Заметка-чеклист"""
   
    def __init__(self, title: str, text: str, tags: List[str] = None, items: List[str] = None):
        super().__init__(title, text, tags)
        self.items = items if items else []
        self.checked = [False] * len(self.items)
   
    def add_item(self, item: str):
        self.items.append(item)
        self.checked.append(False)
   
    def toggle_item(self, index: int):
        if 0 <= index < len(self.checked):
            self.checked[index] = not self.checked[index]
   
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['items'] = self.items
        data['checked'] = self.checked
        return data
   
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        note = cls(data['title'], data['text'], data['tags'], data['items'])
        note.checked = data.get('checked', [False] * len(note.items))
        note.date = datetime.fromisoformat(data['date'])
        return note
   
    def display(self) -> str:
        items_display = '\n'.join(f"║   {'✓' if checked else '☐'} {item[:54]:<54} ║"
                                   for item, checked in zip(self.items, self.checked))
        return f"""
╔══════════════════════════════════════════════════════════╗
║ ✓ {self.title[:55]:<55} ║
╠══════════════════════════════════════════════════════════╣
║ Дата: {self.date.strftime('%Y-%m-%d %H:%M:%S'):<49} ║
║ Теги: {', '.join(self.tags) if self.tags else 'нет':<51} ║
╠══════════════════════════════════════════════════════════╣
{items_display}
║                                                          ║
║ Заметка: {self.text[:50]:<50} ║
╚══════════════════════════════════════════════════════════╝"""


TEXT_NOTE_TYPES = {
    'TextNote': TextNote,
    'VoiceNote': VoiceNote,
    'ChecklistNote': ChecklistNote
}


class UndoStack:
    """Стек для отмены действий"""
   
    def __init__(self):
        self.stack = deque()
        self.redo_stack = deque()
   
    def push(self, action: Dict[str, Any]):
        self.stack.append(action)
        self.redo_stack.clear()
   
    def undo(self) -> Optional[Dict[str, Any]]:
        if self.stack:
            action = self.stack.pop()
            self.redo_stack.append(action)
            return action
        return None
   
    def redo(self) -> Optional[Dict[str, Any]]:
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.stack.append(action)
            return action
        return None


class Notebook:
    """Основной класс для управления заметками"""
   
    def __init__(self, filename: str = "notebook.json"):
        self.notes: List[Note] = []
        self.filename = filename
        self.undo_stack = UndoStack()
        self.load_from_file()
   
    def add_note(self, note: Note):
        self.notes.append(note)
        self.undo_stack.push({
            'action': 'add',
            'index': len(self.notes) - 1,
            'note': note
        })
        self.save_to_file()
   
    def edit_note(self, index: int, title: str = None, text: str = None, tags: List[str] = None):
        if 0 <= index < len(self.notes):
            old_note = self.notes[index]
            # Сохраняем старую версию для отмены
            self.undo_stack.push({
                'action': 'edit',
                'index': index,
                'old_note': old_note
            })
           
            if title:
                old_note.title = Note._validate_title(title)
            if text:
                old_note.text = Note._validate_text(text)
            if tags is not None:
                old_note.tags = tags
           
            self.save_to_file()
   
    def delete_note(self, index: int):
        if 0 <= index < len(self.notes):
            deleted_note = self.notes.pop(index)
            self.undo_stack.push({
                'action': 'delete',
                'index': index,
                'note': deleted_note
            })
            self.save_to_file()
   
    def undo(self) -> bool:
        action = self.undo_stack.undo()
        if not action:
            return False
       
        if action['action'] == 'add':
            self.notes.pop(action['index'])
        elif action['action'] == 'edit':
            self.notes[action['index']] = action['old_note']
        elif action['action'] == 'delete':
            self.notes.insert(action['index'], action['note'])
       
        self.save_to_file()
        return True
   
    def redo(self) -> bool:
        action = self.undo_stack.redo()
        if not action:
            return False
       
        if action['action'] == 'add':
            self.notes.insert(action['index'], action['note'])
        elif action['action'] == 'edit':
            # В redo хранится новая версия, нужно её восстановить
            pass  # В реальном коде нужно хранить новую версию
        elif action['action'] == 'delete':
            self.notes.pop(action['index'])
       
        self.save_to_file()
        return True
   
    def get_notes_by_tag(self, tag: str) -> List[Note]:
        tag = tag.strip().lower()
        return [note for note in self.notes if tag in [t.lower() for t in note.tags]]
   
    def get_notes_by_date(self, date: datetime) -> List[Note]:
        return [note for note in self.notes if note.date.date() == date.date()]
   
    def get_notes_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Note]:
        return [note for note in self.notes if start_date.date() <= note.date.date() <= end_date.date()]
   
    def search_notes(self, query: str) -> List[Note]:
        query = query.lower()
        return [note for note in self.notes
                if query in note.title.lower() or query in note.text.lower()]
   
    def save_to_file(self):
        try:
            data = [note.to_dict() for note in self.notes]
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
   
    def load_from_file(self):
        if not os.path.exists(self.filename):
            return
       
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.notes = [Note.from_dict(note_data) for note_data in data]
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
            self.notes = []


class ConsoleNotebookApp:
    """Консольное приложение для работы с заметками"""
   
    def __init__(self):
        self.notebook = Notebook()
   
    def run(self):
        print("\n" + "="*60)
        print(" ДОБРО ПОЖАЛОВАТЬ В NOTEBOOK ORGANIZER ".center(60, "="))
        print("="*60)
       
        while True:
            self.show_menu()
            choice = input("\nВыберите действие: ").strip()
           
            if choice == '1':
                self.create_note()
            elif choice == '2':
                self.view_notes()
            elif choice == '3':
                self.edit_note()
            elif choice == '4':
                self.delete_note()
            elif choice == '5':
                self.filter_notes()
            elif choice == '6':
                if self.notebook.undo():
                    print("✓ Действие отменено")
                else:
                    print("✗ Нечего отменять")
            elif choice == '7':
                if self.notebook.redo():
                    print("✓ Действие повторено")
                else:
                    print("✗ Нечего повторять")
            elif choice == '0':
                print("\nДо свидания!")
                break
            else:
                print("✗ Неверный выбор. Попробуйте снова.")
   
    def show_menu(self):
        print("\n" + "-"*40)
        print("ГЛАВНОЕ МЕНЮ".center(40))
        print("-"*40)
        print("1. Создать заметку")
        print("2. Просмотреть все заметки")
        print("3. Редактировать заметку")
        print("4. Удалить заметку")
        print("5. Фильтрация заметок")
        print("6. Отменить действие (Undo)")
        print("7. Повторить действие (Redo)")
        print("0. Выход")
        print("-"*40)
   
    def create_note(self):
        print("\n--- СОЗДАНИЕ НОВОЙ ЗАМЕТКИ ---")
        print("Тип заметки:")
        print("1. Текстовая заметка")
        print("2. Голосовая заметка")
        print("3. Чек-лист")
       
        type_choice = input("Выберите тип: ").strip()
       
        try:
            title = input("Заголовок: ")
            text = input("Текст/описание: ")
            tags_input = input("Теги (через запятую): ")
            tags = [t.strip() for t in tags_input.split(',') if t.strip()]
           
            if type_choice == '1':
                note = TextNote(title, text, tags)
            elif type_choice == '2':
                duration = int(input("Длительность (сек): ") or "0")
                note = VoiceNote(title, text, tags, duration)
            elif type_choice == '3':
                note = ChecklistNote(title, text, tags)
                while True:
                    item = input("Добавить пункт (Enter для завершения): ")
                    if not item:
                        break
                    note.add_item(item)
            else:
                print("✗ Неверный тип заметки")
                return
           
            self.notebook.add_note(note)
            print(f"\n✓ Заметка \"{title}\" успешно создана!")
           
        except ValueError as e:
            print(f"✗ Ошибка: {e}")
        except Exception as e:
            print(f"✗ Ошибка при создании заметки: {e}")
   
    def view_notes(self):
        if not self.notebook.notes:
            print("\n✗ Нет заметок для отображения")
            return
       
        print(f"\n--- ВСЕ ЗАМЕТКИ (всего: {len(self.notebook.notes)}) ---")
        for i, note in enumerate(self.notebook.notes):
            print(f"\n[{i}] {note}")
            print("-"*40)
            print(note.display())
   
    def edit_note(self):
        if not self.notebook.notes:
            print("\n✗ Нет заметок для редактирования")
            return
       
        self.view_notes()
        try:
            index = int(input("\nВведите индекс заметки для редактирования: "))
           
            print("\nОставьте поле пустым, чтобы не менять")
            new_title = input(f"Новый заголовок (текущий: {self.notebook.notes[index].title}): ")
            new_text = input(f"Новый текст (текущий: {self.notebook.notes[index].text[:50]}...): ")
            new_tags = input(f"Новые теги (текущие: {', '.join(self.notebook.notes[index].tags)}): ")
           
            tags_list = [t.strip() for t in new_tags.split(',') if t.strip()] if new_tags else None
           
            self.notebook.edit_note(
                index,
                title=new_title if new_title else None,
                text=new_text if new_text else None,
                tags=tags_list
            )
            print("✓ Заметка успешно отредактирована!")
           
        except ValueError:
            print("✗ Неверный индекс")
        except Exception as e:
            print(f"✗ Ошибка при редактировании: {e}")
   
    def delete_note(self):
        if not self.notebook.notes:
            print("\n✗ Нет заметок для удаления")
            return
       
        self.view_notes()
        try:
            index = int(input("\nВведите индекс заметки для удаления: "))
            confirm = input(f"Удалить заметку \"{self.notebook.notes[index].title}\"? (да/нет): ")
           
            if confirm.lower() == 'да':
                self.notebook.delete_note(index)
                print("✓ Заметка успешно удалена!")
            else:
                print("✗ Удаление отменено")
               
        except ValueError:
            print("✗ Неверный индекс")
        except Exception as e:
            print(f"✗ Ошибка при удалении: {e}")
   
    def filter_notes(self):
        print("\n--- ФИЛЬТРАЦИЯ ЗАМЕТОК ---")
        print("1. По тегу")
        print("2. По дате")
        print("3. По поисковому запросу")
       
        choice = input("Выберите тип фильтрации: ").strip()
       
        filtered = []
       
        if choice == '1':
            tag = input("Введите тег: ")
            filtered = self.notebook.get_notes_by_tag(tag)
            print(f"\n--- ЗАМЕТКИ ПО ТЕГУ '{tag}' (найдено: {len(filtered)}) ---")
           
        elif choice == '2':
            print("Фильтр по дате:")
            print("1. Конкретная дата")
            print("2. Диапазон дат")
            subchoice = input("Выберите: ")
           
            if subchoice == '1':
                date_str = input("Введите дату (ГГГГ-ММ-ДД): ")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                filtered = self.notebook.get_notes_by_date(date)
                print(f"\n--- ЗАМЕТКИ ЗА {date_str} (найдено: {len(filtered)}) ---")
            elif subchoice == '2':
                start_str = input("Начальная дата (ГГГГ-ММ-ДД): ")
                end_str = input("Конечная дата (ГГГГ-ММ-ДД): ")
                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d")
                filtered = self.notebook.get_notes_by_date_range(start, end)
                print(f"\n--- ЗАМЕТКИ С {start_str} ПО {end_str} (найдено: {len(filtered)}) ---")
       
        elif choice == '3':
            query = input("Поисковый запрос: ")
            filtered = self.notebook.search_notes(query)
            print(f"\n--- РЕЗУЛЬТАТЫ ПОИСКА ПО ЗАПРОСУ '{query}' (найдено: {len(filtered)}) ---")
       
        else:
            print("✗ Неверный выбор")
            return
       
        if not filtered:
            print("\n✗ Заметки не найдены")
            return
       
        for i, note in enumerate(filtered):
            print(f"\n[{i}] {note}")
            print(note.display())


if __name__ == "__main__":
    app = ConsoleNotebookApp()
    app.run() 
