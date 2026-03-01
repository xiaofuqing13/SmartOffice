import AlignCenter from './AlignCenter.vue';
import AlignLeft from './AlignLeft.vue';
import AlignRight from './AlignRight.vue';
import Bold from './Bold.vue';
import CheckboxButton from './CheckboxButton.vue';
import Inbox from './Inbox.vue';
import Italic from './Italic.vue';
import Save from './Save.vue';
import Underline from './Underline.vue';

export {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  CheckboxButton,
  Inbox,
  Italic,
  Save,
  Underline
};

// 注册自定义图标组件
export function registerCustomIcons(app) {
  app.component('AlignCenter', AlignCenter);
  app.component('AlignLeft', AlignLeft);
  app.component('AlignRight', AlignRight);
  app.component('Bold', Bold);
  app.component('CheckboxButton', CheckboxButton);
  app.component('Inbox', Inbox);
  app.component('Italic', Italic);
  app.component('Save', Save);
  app.component('Underline', Underline);
} 