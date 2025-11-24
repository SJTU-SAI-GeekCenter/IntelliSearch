export enum TOOL {
  SEARCH_BOOK = 'search-book',
  LIST_BOOK_REVIEWS = 'list-book-reviews',
  SEARCH_MOVIE = 'search-movie',
  LIST_MOVIE_REVIEWS = 'list-movie-reviews',
  BROWSE = 'browse',
  LIST_GROUP_TOPICS = 'list-group-topics',
  GET_GROUP_TOPIC_DETAIL = 'get-group-topic-detail'
}

export declare namespace Douban {
  interface Book {
    rating: {
      max: number
      numRaters: number
      average: string
      min: number
    }
    subtitle: string
    author: string[]
    pubdate: string
    tags: {
      count: number
      name: string
      title: string
    }[]
    origin_title: string
    image: string
    binding: string
    translator: any[]
    catalog: string
    pages: string
    images: {
      small: string
      large: string
      medium: string
    }
    alt: string
    id: string
    publisher: string
    isbn10: string
    isbn13: string
    title: string
    url: string
    alt_title: string
    author_intro: string
    summary: string
    series: {
      id: string
      title: string
    }
    price: string
    ebook_url: string
  }

  interface BookReview {
    rating: {
      count: number;
      max: number;
      star_count: number;
      value: number;
    } | null;
    useful_count: number;
    sharing_url: string;
    title: string;
    url: string;
    abstract: string;
    uri: string;
    ad_info: null;
    topic: null;
    photos: any[];
    reactions_count: number;
    comments_count: number;
    user: {
      kind: string;
      name: string;
      url: string;
      uri: string;
      avatar: string;
      is_club: boolean;
      type: string;
      id: string;
      uid: string;
    };
    create_time: string;
    reshares_count: number;
    type: string;
    id: string;
    subject: {
      press: string[];
      type: string;
      pubdate: string[];
      title: string;
    };
  
  }

  interface Movie {
    /** 条目 id */
    id: string;
    /** 中文名 */
    title: string;
    /** 原名 */
    original_title: string;
    /** 条目 URL */
    alt: string;
    /** 
     * 电影海报图，分别提供 288px x 465px(大)，96px x 155px(中) 64px x 103px(小)尺寸 
     */
    images: {
      small: string;
      medium: string;
      large: string;
    };
    /** 评分信息 */
    rating: {
      /** 平均评分 */
      average: number;
      /** 评分人数 */
      numRaters?: number;
      /** 评分人数（别名） */
      ratings_count?: number;
    };
    /** 如果条目类型是电影则为上映日期，如果是电视剧则为首播日期 */
    pubdates: string[];
    /** 年代 */
    year: string;
    /** 条目分类, movie 或者 tv */
    subtype: 'movie' | 'tv';
  }

  interface MovieReview {
    id: string
    title: string
    alt: string
    subject_id: string
    author: {
      id: string
      name: string
      uid: string
      signature: string
      alt: string
      avatar: string
    }[]
    rating: {
      max: number
      numRaters: number
      average: string
      min: number
    }
    summary: string
  }

  interface Topic {
    update_time: string
    is_event: boolean
    is_elite: boolean
    title: string
    url: string
    topic_tags: { id: string; name: string }[]
    author: any[]
    uri: string
    cover_url: string
    id: string
    create_time: string
    comments_count: number
    activity_tag: null
    gallery_topic: null
    label: string
    type: string
    is_ad: boolean
  }

  interface TopicDetail extends Topic {
    like_count: number
    comments_count: number
    collections_count: number
    reshares_count: number
    content: string
    abstract: string
  }
}