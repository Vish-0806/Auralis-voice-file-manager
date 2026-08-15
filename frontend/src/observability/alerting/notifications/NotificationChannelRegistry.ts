import { INotificationChannel } from '../interfaces/notification-channel';
import { AlertNotificationError } from '../errors/AlertingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class NotificationChannelRegistry {
  private readonly _channels = new Map<string, INotificationChannel>();

  public register(channel: INotificationChannel): void {
    if (!channel) {
      throw new AlertNotificationError('Channel cannot be null or undefined');
    }
    if (!channel.id) {
      throw new AlertNotificationError('Channel ID must be a valid non-empty string');
    }
    if (this._channels.has(channel.id)) {
      throw new AlertNotificationError(`Channel with ID ${channel.id} already exists`);
    }

    this._channels.set(channel.id, channel);
  }

  public unregister(channelId: string): void {
    if (!channelId) {
      throw new AlertNotificationError('Channel ID is required');
    }
    if (!this._channels.has(channelId)) {
      throw new AlertNotificationError(`Channel with ID ${channelId} not found`);
    }
    this._channels.delete(channelId);
  }

  public get(channelId: string): INotificationChannel | null {
    return this._channels.get(channelId) || null;
  }

  public has(channelId: string): boolean {
    return this._channels.has(channelId);
  }

  public list(): ReadonlyArray<INotificationChannel> {
    return freezeDeepSafe(Array.from(this._channels.values()));
  }

  public enable(channelId: string): void {
    const channel = this.get(channelId);
    if (!channel) {
      throw new AlertNotificationError(`Channel with ID ${channelId} not found`);
    }
    channel.enabled = true;
  }

  public disable(channelId: string): void {
    const channel = this.get(channelId);
    if (!channel) {
      throw new AlertNotificationError(`Channel with ID ${channelId} not found`);
    }
    channel.enabled = false;
  }

  public clear(): void {
    this._channels.clear();
  }
}
