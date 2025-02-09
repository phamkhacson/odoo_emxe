import logging
from itertools import chain
from lxml import etree
from lxml.builder import E
from odoo import api, models, _
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

_logger = logging.getLogger(__name__)
USER_PRIVATE_FIELDS = []
MIN_ROUNDS = 350000
concat = chain.from_iterable


def name_selection_groups(ids):
    return 'sel_groups_' + '_'.join(str(it) for it in sorted(ids))


def name_boolean_group(id):
    return 'in_group_' + str(id)


class ResGroups(models.Model):
    _inherit = 'res.groups'

    @api.model
    def _update_user_groups_view(self):
        """ Modify the view with xmlid ``base.user_groups_view``, which inherits
            the user form view, and introduces the reified group fields.
        """
        # remove the language to avoid translations, it will be handled at the view level
        self = self.with_context(lang=None)

        # We have to try-catch this, because at first init the view does not
        # exist but we are already creating some basic groups.
        view = self.env.ref('base.user_groups_view', raise_if_not_found=False)
        if not (view and view._name == 'ir.ui.view'):
            return

        if self._context.get('install_filename') or self._context.get(MODULE_UNINSTALL_FLAG):
            # use a dummy view during install/upgrade/uninstall
            xml = E.field(name="groups_id", position="after")

        else:
            group_no_one = view.env.ref('base.group_no_one')
            group_employee = view.env.ref('base.group_user')
            xml0, xml1, xml2, xml3, xml4 = [], [], [], [], []
            xml_by_category = {}
            xml1.append(E.separator(string='User Type', colspan="2", groups='base.group_no_one'))

            user_type_field_name = ''
            user_type_readonly = str({})
            sorted_tuples = sorted(self.get_groups_by_application(),
                                   key=lambda t: t[0].xml_id != 'base.module_category_user_type')
            for app, kind, gs, category_name in sorted_tuples:  # we process the user type first
                attrs = {}
                # hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
                if app.xml_id in self._get_hidden_extra_categories():
                    attrs['groups'] = 'base.group_no_one'

                # User type (employee, portal or public) is a separated group. This is the only 'selection'
                # group of res.groups without implied groups (with each other).
                if app.xml_id == 'base.module_category_user_type':
                    # application name with a selection field
                    field_name = name_selection_groups(gs.ids)
                    # test_reified_groups, put the user category type in invisible
                    # as it's used in domain of attrs of other fields,
                    # and the normal user category type field node is wrapped in a `groups="base.no_one"`,
                    # and is therefore removed when not in debug mode.
                    xml0.append(E.field(name=field_name, invisible="1", on_change="1"))
                    user_type_field_name = field_name
                    user_type_readonly = str({'readonly': [(user_type_field_name, '!=', group_employee.id)]})
                    attrs['widget'] = 'radio'
                    # Trigger the on_change of this "virtual field"
                    attrs['on_change'] = '1'
                    xml1.append(E.field(name=field_name, **attrs))
                    xml1.append(E.newline())

                elif kind == 'selection':
                    # application name with a selection field
                    field_name = name_selection_groups(gs.ids)
                    attrs['attrs'] = user_type_readonly
                    attrs['on_change'] = '1'
                    if category_name not in xml_by_category:
                        xml_by_category[category_name] = []
                        xml_by_category[category_name].append(E.newline())
                    xml_by_category[category_name].append(E.field(name=field_name, **attrs))
                    xml_by_category[category_name].append(E.newline())

                else:
                    # application separator with boolean fields
                    app_name = app.name or 'Other'
                    # dungnh: if app_name != 'Other'
                    if app_name != 'Other':
                        xml3.append(E.separator(string=app_name, colspan="4", **attrs))
                    attrs['attrs'] = user_type_readonly
                    left_group, right_group = [], []
                    group_count = 0
                    for g in gs:
                        field_name = name_boolean_group(g.id)
                        dest_group = left_group if group_count % 2 == 0 else right_group
                        if g == group_no_one:
                            # make the group_no_one invisible in the form view
                            dest_group.append(E.field(name=field_name, invisible="1", **attrs))
                        # start dungnh
                        elif g == view.env.ref('base.group_sanitize_override'):
                            dest_group.append(E.field(name=field_name, invisible="1", **attrs))
                        # end dungnh
                        else:
                            dest_group.append(E.field(name=field_name, **attrs))
                        group_count += 1
                    xml3.append(E.group(*left_group))
                    xml3.append(E.group(*right_group))
            xml3.append({'class': "o_label_nowrap"})
            if user_type_field_name:
                user_type_attrs = {'invisible': [(user_type_field_name, '!=', group_employee.id)]}
            else:
                user_type_attrs = {}
            for xml_cat in sorted(xml_by_category.keys(), key=lambda it: it[0]):
                master_category_name = xml_cat[1]
                xml2.append(E.group(*(xml_by_category[xml_cat]), col="2", string=master_category_name))
            xml = E.field(
                *(xml0),
                E.group(*(xml1), groups="base.group_no_one"),
                E.group(*(xml2), attrs=str(user_type_attrs)),
                E.group(*(xml3), attrs=str(user_type_attrs)),
                E.group(*(xml4), attrs=str(user_type_attrs), groups="base.group_no_one"), name="groups_id", position="replace")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))

        # serialize and update the view
        xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
        if xml_content != view.arch:  # avoid useless xml validation if no change
            new_context = dict(view._context)
            new_context.pop('install_filename', None)  # don't set arch_fs for this computed view
            new_context['lang'] = None
            view.with_context(new_context).write({'arch': xml_content})
