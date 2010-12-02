from adminbrowse.base import (ChangeListColumn, ChangeListTemplateColumn,
                              ChangeListModelFieldColumn)
from adminbrowse.related import ChangeLink, ChangeListLink, RelatedList
from adminbrowse.columns import URLColumn, TruncatedFieldColumn


template_column = ChangeListTemplateColumn
model_field = ChangeListModelFieldColumn
link_to_change = ChangeLink
related_list = RelatedList
link_to_changelist = ChangeListLink
link_to_url = URLColumn
truncated_field = TruncatedFieldColumn

