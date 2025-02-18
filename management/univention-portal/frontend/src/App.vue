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
  <cookie-banner
    v-if="showCookieBanner"
    @dismissed="hideCookieBanner"
  />
  <router-view />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import CookieBanner from '@/components/globals/CookieBanner.vue';

import { getCookie } from '@/jsHelper/tools';
import { login } from '@/jsHelper/login';
import { mapGetters } from 'vuex';

interface AppData {
  cookieBannerDismissed: boolean,
}

export default defineComponent({
  name: 'App',
  components: {
    CookieBanner,
  },
  data(): AppData {
    return {
      cookieBannerDismissed: false,
    };
  },
  computed: {
    ...mapGetters({
      userState: 'user/userState',
      metaData: 'metaData/getMeta',
    }),
    showCookieBanner(): boolean {
      const cookieName = this.metaData.cookieBanner.cookie || 'univentionCookieSettingsAccepted';
      let domainShouldShowBanner = true;
      if (this.metaData.cookieBanner.domains.length > 0) {
        domainShouldShowBanner = false;
        this.metaData.cookieBanner.domains.forEach((dom) => {
          if (document.domain.endsWith(dom)) {
            domainShouldShowBanner = true;
          }
        });
      }
      return this.metaData.cookieBanner.show && domainShouldShowBanner && !getCookie(cookieName) && !this.cookieBannerDismissed;
    },
  },
  async mounted() {
    // Set locale and load portal data from backend
    this.$store.dispatch('activateLoadingState');
    const answer = await this.$store.dispatch('loadPortal', {
      adminMode: false,
    });

    if (this.metaData.title) {
      document.title = this.metaData.title;
    }
    if (this.metaData.favicon) {
      this.setFavicon(this.metaData.favicon);
    }

    if (answer.portal && answer.portal.ensureLogin && !this.userState.username) {
      login(this.userState);
    }

    this.$store.dispatch('deactivateLoadingState');
  },
  methods: {
    hideCookieBanner(): void {
      this.cookieBannerDismissed = true;
    },
    setFavicon(href): void {
      const icon = (document.querySelector('link[rel="shortcut icon"]') || document.querySelector('link[rel="icon"]')) as HTMLLinkElement | null;
      if (icon) {
        icon.href = href;
      }
    },
  },
});
</script>

<style lang=stylus>
*
  ::-webkit-scrollbar
    width: 0.25rem
  ::-webkit-scrollbar-track
    background: var(--portal-scrollbar-background)
  ::-webkit-scrollbar-thumb
    background: var(--font-color-contrast-low)
    border-radius: 2rem
  ::-webkit-scrollbar-thumb:hover
    background: var(--font-color-contrast-middle)
</style>
