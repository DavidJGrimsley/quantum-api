from quantum_api.enums import EchoType
from quantum_api.services.quantum_word_dictionary import get_quantum_category_for_word


def test_dictionary_quantum_interference_mapping():
    assert get_quantum_category_for_word("memory") == EchoType.QUANTUM_INTERFERENCE


def test_dictionary_quantum_gates_mapping():
    assert get_quantum_category_for_word("circuit") == EchoType.QUANTUM_GATES


def test_dictionary_quantum_entanglement_mapping():
    assert get_quantum_category_for_word("entangled") == EchoType.QUANTUM_ENTANGLEMENT


def test_dictionary_original_mapping_for_common_word():
    assert get_quantum_category_for_word("hello") == EchoType.ORIGINAL
