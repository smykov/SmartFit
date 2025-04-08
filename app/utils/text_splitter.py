from typing import List


class TextSplitter:
    """
    Утилита для интеллектуального разбиения текста на части
    """

    def split_text(self, text: str, max_size: int) -> List[str]:
        """
        Разбивает текст на части с учетом структуры текста

        Args:
            text: Исходный текст
            max_size: Максимальный размер части

        Returns:
            List[str]: Список частей текста
        """
        # Если текст помещается целиком
        if len(text) <= max_size:
            return [text]

        parts = []
        current_part = ""

        # Разбиваем по параграфам
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            # Если параграф слишком большой, разбиваем по строкам
            if len(paragraph) > max_size:
                lines = paragraph.split('\n')

                for line in lines:
                    # Если строка слишком большая, разбиваем по предложениям
                    if len(line) > max_size:
                        sentences = self._split_into_sentences(line)

                        for sentence in sentences:
                            # Если предложение слишком большое, разбиваем механически
                            if len(sentence) > max_size:
                                for i in range(0, len(sentence), max_size):
                                    chunk = sentence[i:i + max_size]

                                    # Если текущая часть + чанк превышает лимит
                                    if len(current_part) + len(chunk) > max_size:
                                        parts.append(current_part.strip())
                                        current_part = chunk + " "
                                    else:
                                        current_part += chunk + " "
                            else:
                                # Если предложение помещается
                                if len(current_part) + len(sentence) > max_size:
                                    parts.append(current_part.strip())
                                    current_part = sentence + " "
                                else:
                                    current_part += sentence + " "
                    else:
                        # Если строка помещается
                        if len(current_part) + len(line) + 1 > max_size:
                            parts.append(current_part.strip())
                            current_part = line + "\n"
                        else:
                            current_part += line + "\n"
            else:
                # Если параграф помещается
                if len(current_part) + len(paragraph) + 2 > max_size:
                    parts.append(current_part.strip())
                    current_part = paragraph + "\n\n"
                else:
                    current_part += paragraph + "\n\n"

        # Добавляем последнюю часть, если она не пуста
        if current_part.strip():
            parts.append(current_part.strip())

        return parts

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Разбивает текст на предложения

        Args:
            text: Исходный текст

        Returns:
            List[str]: Список предложений
        """
        # Простое разбиение по точкам
        # В реальном приложении здесь может быть более сложная логика
        sentences = []
        current = ""

        for char in text:
            current += char
            if char in ['.', '!', '?'] and len(current) > 1:
                sentences.append(current)
                current = ""

        # Добавляем последнее предложение, если оно не пусто
        if current:
            sentences.append(current)

        return sentences