from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute, BooleanAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from uuid import uuid4
from datetime import datetime
from pynamodb.transactions import TransactWrite
from pynamodb.connection import Connection

import os


class CreatedDateIndex(GlobalSecondaryIndex):
    class Meta:
        projection = AllProjection()
        read_capacity_units = 1
        write_capacity_units = 1

    id = UnicodeAttribute(hash_key=True)
    created_date = UTCDateTimeAttribute(range_key=True)

class SequenceNumberIndex(GlobalSecondaryIndex):
    class Meta:
        projection = AllProjection()
        read_capacity_units = 1
        write_capacity_units = 1

    dummy_hash_key = NumberAttribute(hash_key=True, default=0)
    sequence_number = NumberAttribute(range_key=True)

class MTGCard(Model):
    class Meta:
        table_name = "mtg_card_test" if os.environ.get('IS_DEBUG') else 'mtg_card'
        region = 'us-east-1'  # update this to your AWS region
    # Plumbing
    id = UnicodeAttribute(hash_key=True, default=lambda: str(uuid4()))
    created_date = UTCDateTimeAttribute(default=datetime.utcnow)
    created_date_index = CreatedDateIndex()
    
    # Function definition
    card_name = UnicodeAttribute(default='Missing')
    mana_cost = UnicodeAttribute(null=True)
    rules_text = UnicodeAttribute(null=True)
    card_type = UnicodeAttribute(default='Artifact')
    flavor_text = UnicodeAttribute(null=True)
    rarity = UnicodeAttribute(default='Common')
    power = NumberAttribute(null=True)
    toughness = NumberAttribute(null=True)
    art_description = UnicodeAttribute(null=True)
    explanation = UnicodeAttribute(null=True)
    
    @property
    def card_details(self):
        return {
            'card_name': self.card_name,
            'mana_cost': self.mana_cost,
            'rules_text': self.rules_text,
            'card_type': self.card_type,
            'flavor_text': self.flavor_text,
            'rarity': self.rarity,
            'power': self.power,
            'toughness': self.toughness,
            'art_description': self.art_description,
            'explanation': self.explanation
        }
    
    # Meta
    prompt = UnicodeAttribute(null=True)
    art_url = UnicodeAttribute(null=True)
    final_rendered_url = UnicodeAttribute(null=True)

    is_deleted = BooleanAttribute(default=False)
    is_finished_generating = BooleanAttribute(default=False)
    is_superseded = BooleanAttribute(default=False)
    parent_id = UnicodeAttribute(null=True)

    @property
    def should_show(self):
        return not self.is_deleted and self.is_finished_generating and not self.is_superseded

    creator_id = UnicodeAttribute(null=True)

    sequence_number = NumberAttribute(null=True)
    sequence_number_index = SequenceNumberIndex()

    dummy_hash_key = NumberAttribute(default=0)
    
    @classmethod
    def get_latest(cls, n=10):
        return cls.sequence_number_index.query(0, limit=n, scan_index_forward=False)

    @classmethod
    def create_next_sequence_number(cls):
        connection = Connection()
        with TransactWrite(connection=connection) as transaction:
            sentinel_row = cls('00000000-0000-0000-0000-000000000000')
            transaction.update(
                sentinel_row,
                actions=[
                    cls.sequence_number.add(1)
                ]
            )
        # Requery the row to get the updated sequence_number
        updated_row = cls.get('00000000-0000-0000-0000-000000000000')
        return updated_row.sequence_number - 1
    
    @classmethod
    def init_new_row(cls, description, parent_id, creator_id):
        new_sequence_number = cls.create_next_sequence_number()
        new_row = cls()
        new_row.sequence_number = new_sequence_number
        new_row.prompt = description
        new_row.parent_id = parent_id
        new_row.creator_id = creator_id
        new_row.save()
        return new_row
    

    @property
    def json_values(self):
        return {key: value for key,value in self.attribute_values.items()
                if key != 'created_date'}

    # def __str__

if __name__ == '__main__':
    if not MTGCard.exists():
        MTGCard.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
        sentinel_row = MTGCard('00000000-0000-0000-0000-000000000000')
        sentinel_row.sequence_number = 1
        sentinel_row.save()
        