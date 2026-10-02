from django.test import SimpleTestCase

from ecoles.utils import (
    amount_in_words,
    format_amount,
    normalize_phone,
    number_to_french,
    render_message,
    whatsapp_url,
)


class NumberToFrenchTests(SimpleTestCase):
    def test_reference_values(self):
        cases = {
            0: "zéro",
            1: "un",
            16: "seize",
            17: "dix-sept",
            21: "vingt et un",
            71: "soixante et onze",
            77: "soixante-dix-sept",
            80: "quatre-vingts",
            81: "quatre-vingt-un",
            91: "quatre-vingt-onze",
            100: "cent",
            101: "cent un",
            200: "deux cents",
            201: "deux cent un",
            1000: "mille",
            1001: "mille un",
            2000: "deux mille",
            25000: "vingt-cinq mille",
            80000: "quatre-vingt mille",
            200000: "deux cent mille",
            280000: "deux cent quatre-vingt mille",
            1000000: "un million",
            2500000: "deux millions cinq cent mille",
            80000000: "quatre-vingts millions",
            200000000: "deux cents millions",
            1000000000: "un milliard",
        }
        for number, words in cases.items():
            with self.subTest(number=number):
                self.assertEqual(number_to_french(number), words)

    def test_amount_in_words(self):
        self.assertEqual(amount_in_words(75000), "soixante-quinze mille francs CFA")
        self.assertEqual(amount_in_words(1000000), "un million de francs CFA")
        self.assertEqual(amount_in_words(1200000), "un million deux cent mille francs CFA")
        self.assertEqual(amount_in_words(1, "XOF"), "un franc CFA")
        self.assertEqual(amount_in_words(500000, "GNF"), "cinq cent mille francs guinéens")


class PhoneTests(SimpleTestCase):
    def test_cote_divoire_keeps_leading_zero(self):
        self.assertEqual(normalize_phone("07 07 07 07 07", "CI"), "2250707070707")
        self.assertEqual(normalize_phone("+225 07 07 07 07 07", "CI"), "2250707070707")
        self.assertEqual(normalize_phone("00225 0707070707", "CI"), "2250707070707")
        self.assertEqual(normalize_phone("2250707070707", "CI"), "2250707070707")

    def test_old_eight_digit_ivorian_number_is_rejected(self):
        self.assertIsNone(normalize_phone("07 07 07 07", "CI"))

    def test_other_countries(self):
        self.assertEqual(normalize_phone("77 123 45 67", "SN"), "221771234567")
        self.assertEqual(normalize_phone("6 77 12 34 56", "CM"), "237677123456")
        self.assertEqual(normalize_phone("0812345678", "CD"), "243812345678")
        self.assertEqual(normalize_phone("90 12 34 56", "TG"), "22890123456")

    def test_empty_or_garbage(self):
        self.assertIsNone(normalize_phone("", "CI"))
        self.assertIsNone(normalize_phone("pas de numéro", "CI"))


class MiscTests(SimpleTestCase):
    def test_format_amount(self):
        self.assertEqual(format_amount(1250000), "1 250 000")
        self.assertEqual(format_amount(-5000), "-5 000")

    def test_render_message_ignores_unknown_and_attribute_access(self):
        text = render_message("{eleve} doit {montant} {inconnu} {eleve.__class__}", {"eleve": "Aya", "montant": "5"})
        self.assertEqual(text, "Aya doit 5 {inconnu} {eleve.__class__}")

    def test_whatsapp_url(self):
        self.assertEqual(whatsapp_url("2250707070707", "Bonjour à vous"), "https://wa.me/2250707070707?text=Bonjour%20%C3%A0%20vous")
        self.assertTrue(whatsapp_url(None, "Bonjour").startswith("https://wa.me/?text="))
