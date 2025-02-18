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
  <div
    ref="portal"
    class="portal"
    :class="{
      'portal--play-tile-animation': playTileAnimation,
      'portal--edit-mode': editMode,
    }"
  >
    <screen-reader-announcer />
    <portal-background />
    <portal-header />
    <portal-error
      v-if="errorContentType"
      :error-type="undefined"
    />
    <region
      v-if="!errorContentType"
      v-show="!activeTabId"
      id="portalCategories"
      :aria-role="portalRole"
      class="portal-categories"
    >
      <h2
        v-if="noSearchResults"
        class="portal-category__title"
      >
        {{ NO_SEARCH_RESULTS }}
      </h2>
      <portal-category
        v-for="(category, index) in portalFinalLayoutFiltered"
        :key="category.id"
        :layout-id="category.layoutId"
        :title="category.title"
        :dn="category.dn"
        :virtual="category.virtual"
        :tiles="category.tiles"
        :category-index="index"
      />

      <h2
        v-if="editMode"
        class="portal-category__title"
      >
        <icon-button
          icon="plus"
          class="button--icon--circle button--icon--edit-mode button--shadow"
          :aria-label-prop="ADD_CATEGORY"
          @click="addCategory"
        />
        <span>
          {{ ADD_CATEGORY }}
        </span>
      </h2>
    </region>

    <div
      v-show="activeTabId"
      class="portal-iframes"
      data-test="portal-iframes"
    >
      <portal-iframe
        v-for="tab in tabs"
        :key="tab.id"
        :link="tab.iframeLink"
        :is-active="activeTabId === tab.id"
        :tab-id="tab.id"
        :title="tab.tabLabel"
      />
    </div>

    <notifications :is-in-notification-bar="false" />

    <portal-tool-tip
      v-if="tooltip"
      v-bind="tooltip"
    />
    <portal-sidebar />
    <portal-modal />
    <portal-modal
      :modal-level="2"
    />
    <router-view />
    <loading-overlay />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import Region from '@/components/activity/Region.vue';
import Notifications from '@/components/notifications/Notifications.vue';
import PortalBackground from '@/components/PortalBackground.vue';
import PortalCategory from '@/components/PortalCategory.vue';
import PortalHeader from '@/components/PortalHeader.vue';
import PortalIframe from '@/components/PortalIframe.vue';
import PortalModal from '@/components/modal/PortalModal.vue';
import PortalSidebar from '@/components/PortalSidebar.vue';
import PortalToolTip from '@/components/PortalToolTip.vue';
import ScreenReaderAnnouncer from '@/components/globals/ScreenReaderAnnouncer.vue';
import PortalError from '@/components/globals/PortalError.vue';
import LoadingOverlay from '@/components/globals/LoadingOverlay.vue';

export default defineComponent({
  name: 'Portal',
  components: {
    IconButton,
    LoadingOverlay,
    Notifications,
    PortalBackground,
    PortalCategory,
    PortalHeader,
    PortalIframe,
    PortalModal,
    PortalSidebar,
    PortalToolTip,
    Region,
    ScreenReaderAnnouncer,
    PortalError,
  },
  data(): {playTileAnimation: boolean} {
    return {
      playTileAnimation: true,
    };
  },
  computed: {
    ...mapGetters({
      portalFinalLayoutFiltered: 'portalData/portalFinalLayoutFiltered',
      portalLoaded: 'portalData/loaded',
      errorContentType: 'portalData/errorContentType',
      tabs: 'tabs/allTabs',
      activeTabId: 'tabs/activeTabId',
      editMode: 'portalData/editMode',
      tooltip: 'tooltip/tooltip',
      inFolderModal: 'modal/inFolderModal',
    }),
    ADD_CATEGORY(): string {
      return _('Add category');
    },
    NO_SEARCH_RESULTS(): string {
      return _('No search results');
    },
    noSearchResults(): boolean {
      return this.portalLoaded && this.portalFinalLayoutFiltered.length === 0 && !this.inFolderModal;
    },
    portalRole(): string {
      return this.editMode ? 'application' : '';
    },
  },
  mounted() {
    const portal = this.$refs.portal as HTMLDivElement;
    portal.addEventListener('animationend', this.removeAnimation);
  },
  methods: {
    addCategory() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'CategoryAddModal',
      });
      this.$store.dispatch('activity/setRegion', 'category-add-modal');
    },
    removeAnimation(event: AnimationEvent) {
      const portal = this.$refs.portal as HTMLDivElement;
      if (event.animationName === 'fadeIn') {
        this.playTileAnimation = false;
        portal.removeEventListener('animationend', this.removeAnimation);
      }
    },
  },
});
</script>

<style lang="stylus">
.portal-categories
  position: relative;
  padding: calc(4 * var(--layout-spacing-unit)) calc(6 * var(--layout-spacing-unit));

  @media $mqSmartphone
    padding: calc(4 * var(--layout-spacing-unit)) calc(4 * var(--layout-spacing-unit));

  &__menu-wrapper
    width: 100%
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    justify-content: flex-start;
    align-content: flex-start;
    align-items: flex-start;
    position: absolute

  &__menu-container
    position: relative
    order: 0;
    flex: 0 1 auto;
    align-self: auto;

  &__icon
    position: absolute
    right: 15px
    margin-top: 2px

.portal--edit-mode .portal-categories
  padding-top: calc(6 * var(--layout-spacing-unit))

.portal-iframes
  position: fixed
  top: var(--portal-header-height)
  border: 0 solid var(--portal-iframe-border)
  border-top-width: 0.1rem
  right: 0
  bottom: 0
  left: 0

@keyframes fadeIn
  from
    opacity: 0
    scale: 80%

  to
    opacity: 1
    scale: 100%

.portal--play-tile-animation .portal-tile__box
  animation: fadeIn
  animation-duration: 0.25s
</style>
