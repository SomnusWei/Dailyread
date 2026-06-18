@Observed
export class Article {
  id: number = 0;
  title: string = '';
  content: string = '';
  contentHtml: string | null = null;
  chineseChars: number = 0;
  fontFamily: string = 'default';
  fontSize: number = 16;
  fontColor: string = '#000000';
  isBold: boolean = false;
  isReading: boolean = true;
  isRequired: boolean = false;
  requiredDays: string = '';
  useIndependentCheckRate: boolean = false;
  independentCheckRate: number = 0.0;
  createTime: string = '';
  isLongArticle: boolean = false;
  checkInDays: number = 0;
  completionRate: number = 0;
  imagewebp: string = '';
  lastModified: string = '';

  constructor() {
  }
}
