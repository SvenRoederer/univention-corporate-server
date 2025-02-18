<!--
  Copyright 2021-2024 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
-->
<template>
  <site
    :title="TITLE"
  >
    <my-form
      v-if="formWidgets.length > 0"
      ref="form"
      v-model="formValues"
      :widgets="formWidgetsWithTabindex"
    >
      <footer>
        <button
          type="submit"
          :tabindex="tabindex"
          class="button--primary"
          @click.prevent="submit"
        >
          {{ SUBMIT_LABEL }}
        </button>
      </footer>
    </my-form>
    <error-dialog
      ref="errorDialog"
    />
  </site>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import { umcCommandWithStandby } from '@/jsHelper/umc';
import Site from '@/views/selfservice/Site.vue';
import MyForm from '@/components/forms/Form.vue';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';
import { allValid, initialValue, isEmpty, validateAll, WidgetDefinition } from '@/jsHelper/forms';
import activity from '@/jsHelper/activity';
import { mapGetters } from 'vuex';
import { sanitizeBackendWidget, setBackendInvalidMessage, sanitizeFrontendValues } from '@/views/selfservice/helper';

interface Data {
  formValues: Record<string, unknown>,
  formWidgets: WidgetDefinition[],
}

export default defineComponent({
  name: 'CreateAccount',
  components: {
    Site,
    MyForm,
    ErrorDialog,
  },
  data(): Data {
    return {
      formValues: {},
      formWidgets: [],
    };
  },
  computed: {
    ...mapGetters({
      activityLevel: 'activity/level',
    }),
    TITLE(): string {
      return _('Create an account');
    },
    SUBMIT_LABEL(): string {
      return this.TITLE;
    },
    form(): typeof MyForm {
      return this.$refs.form as typeof MyForm;
    },
    errorDialog(): typeof ErrorDialog {
      return this.$refs.errorDialog as typeof ErrorDialog;
    },
    tabindex(): number {
      return activity(['selfservice'], this.activityLevel);
    },
    formWidgetsWithTabindex(): WidgetDefinition[] {
      return this.formWidgets.map((widget) => {
        widget.tabindex = this.tabindex;
        return widget;
      });
    },
  },
  mounted() {
    umcCommandWithStandby(this.$store, 'passwordreset/get_registration_attributes')
      .then((result) => {
        const sanitized = result.widget_descriptions.map((widget) => sanitizeBackendWidget(widget));
        const passwordIdx = sanitized.findIndex((widget) => widget.type === 'PasswordInputBox');
        const passwordWidget = sanitized[passwordIdx];
        passwordWidget.type = 'PasswordBox';
        const retype = JSON.parse(JSON.stringify(passwordWidget));
        retype.name = `${retype.name}--retype`;
        retype.label = `${retype.label} ${_('(retype)')}`;
        retype.validators = [(widget, value) => (
          isEmpty(widget, value) ? _('Please confirm your new password') : ''
        ), (widget, value, widgets, values) => {
          if (values[passwordWidget.name] !== value) {
            return _('The new passwords do not match');
          }
          return '';
        }];
        sanitized.splice(passwordIdx + 1, 0, retype);
        const values = {};
        sanitized.forEach((widget) => {
          values[widget.name] = initialValue(widget, values[widget.name]);
        });
        this.formWidgets = sanitized;
        this.formValues = values;
        this.$nextTick(() => {
          this.form.focusFirstInteractable();
        });
      }, (error) => {
        this.errorDialog.showError(error.message);
      });
  },
  methods: {
    submit() {
      if (!validateAll(this.formWidgets, this.formValues)) {
        this.form.focusFirstInvalid();
        return;
      }
      umcCommandWithStandby(this.$store, 'passwordreset/create_self_registered_account', {
        attributes: sanitizeFrontendValues(this.formValues, this.formWidgets),
      })
        .then((result) => {
          console.log(result);
          if (result.success) {
            if (result.verifyTokenSuccessfullySend) {
              this.errorDialog.showError([
                _('Hello %(username)s,', { username: result.data.username }),
                _('we have sent you an email to %(email)s. Please follow the instructions in the email to verify your account.', {
                  email: result.data.email,
                }),
              ], _('Account creation successful'), 'dialog')
                .then(() => {
                  this.$router.push({ name: 'selfserviceVerifyAccount', query: { username: result.data.username } });
                });
            } else {
              this.errorDialog.showError([
                _('Hello %(username)s,', { username: result.data.username }),
                _('an error occurred while sending the verification token for your account. Please request a new one.'),
              ])
                .then(() => {
                  this.$router.push({ name: 'selfserviceVerifyAccount', query: { username: result.data.username } });
                });
            }
          } else if (result.failType === 'INVALID_ATTRIBUTES') {
            setBackendInvalidMessage(this.formWidgets, result.data);
            if (!allValid(this.formWidgets)) {
              this.form.focusFirstInvalid();
            }
          } else if (result.failType === 'CREATION_FAILED') {
            this.errorDialog.showError([
              _('Creating a new user failed.'),
              result.data,
            ])
              .then(() => {
                this.form.focusFirstInteractable();
              });
          }
        }, (error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              this.form.focusFirstInteractable();
            });
        });
    },
  },
});
</script>
